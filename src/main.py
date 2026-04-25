"""
LLMéthique - Application Flask principale.

Cette application permet aux chercheurs de l'UQAC de prévalider l'éthique
de leurs projets de recherche à l'aide d'un LLM ancré sur l'EPTC2 (RAG).

Endpoints principaux :
  GET/POST /                         -> dépôt des documents et lancement de l'analyse
  GET      /give_json                -> JSON des réponses du LLM pour la session courante
  GET      /progress                 -> avancement du traitement
  POST     /save_thumbs_vote_db      -> enregistrement d'un vote utilisateur (correcte / incorrecte)
  POST     /save_feedback            -> feedback détaillé sur une réponse

  GET/POST /admin/login              -> formulaire de connexion admin
  GET      /admin/logout             -> déconnexion admin
  GET      /admin/thumbs-votes       -> [protégé] consultation des votes
  GET      /admin/thumbs-votes/export-> [protégé] export CSV des votes
"""

import csv
import json
import os
import re
import sqlite3
import time
from datetime import datetime
from functools import wraps
from io import StringIO
from uuid import uuid4

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_session import Session
from werkzeug.utils import secure_filename

from includes.fonctions.divers import (
    CreerObjetQuestion,
    PdfOrDocx,
    UpdateObjetQuestion,
)
from includes.fonctions.requetellm import requete, requetGrok, requetGrok405B
from includes.objets.DocumentClasse import Document


# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

EXTENSIONS = ['.pdf', '.docx']
DB_PATH = "src/data/llmethique.db"
UPLOAD_FOLDER = 'src/uploads'
SESSION_DIR = "src/data/session"
JSON_OUTPUT_DIR = "src/data/jsonProf"

# Limites de validation
MAX_QUESTION_LEN = 1000
MAX_TEXT_LEN = 2000
ALLOWED_VOTES = {'up', 'down'}
ALLOWED_FEEDBACK_TYPES = {'incorrect', 'incomplete', 'other'}

# Stockage en mémoire de la progression par session
progress_store = {}


# ============================================================================
# BASE DE DONNÉES (SQLite)
# ============================================================================

def init_db():
    """Initialise la base SQLite locale.

    - Crée la table `thumbs_votes` si elle n'existe pas.
    - Détecte si une ancienne table sans contrainte UNIQUE est présente
      et la migre vers la nouvelle structure.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # Création initiale (cas d'une BD neuve)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS thumbs_votes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,
                session_uuid  TEXT,
                question      TEXT NOT NULL,
                vote          TEXT NOT NULL,
                validation    TEXT,
                source        TEXT,
                user_agent    TEXT,
                UNIQUE(session_uuid, question)
            )
            """
        )

        # Migration éventuelle : si la table existe déjà sans la contrainte UNIQUE,
        # on la recrée en préservant les données.
        cur = conn.execute("PRAGMA index_list('thumbs_votes')")
        indexes = [row[1] for row in cur.fetchall()]
        has_unique = any(
            conn.execute(f"PRAGMA index_info('{idx}')").fetchone() is not None
            and conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{idx}'").fetchone()
            for idx in indexes
        )

        # Méthode plus robuste : on tente une insertion qui violerait la contrainte ;
        # si ça passe, c'est qu'elle n'existe pas et il faut migrer.
        if not _has_unique_constraint(conn):
            print("Migration de la BD : ajout de la contrainte UNIQUE...")
            _migrate_add_unique(conn)

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_thumbs_question ON thumbs_votes(question)"
        )
        conn.commit()


def _has_unique_constraint(conn):
    """Vérifie si la table thumbs_votes a la contrainte UNIQUE(session_uuid, question)."""
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='thumbs_votes'"
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return False
    return "UNIQUE" in row[0].upper()


def _migrate_add_unique(conn):
    """Recrée thumbs_votes avec la contrainte UNIQUE en préservant les données."""
    conn.execute("ALTER TABLE thumbs_votes RENAME TO thumbs_votes_old")
    conn.execute(
        """
        CREATE TABLE thumbs_votes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at    TEXT NOT NULL,
            session_uuid  TEXT,
            question      TEXT NOT NULL,
            vote          TEXT NOT NULL,
            validation    TEXT,
            source        TEXT,
            user_agent    TEXT,
            UNIQUE(session_uuid, question)
        )
        """
    )
    # On copie en gardant uniquement la dernière ligne par (session_uuid, question)
    conn.execute(
        """
        INSERT INTO thumbs_votes (
            created_at, session_uuid, question, vote, validation, source, user_agent
        )
        SELECT created_at, session_uuid, question, vote, validation, source, user_agent
        FROM thumbs_votes_old
        WHERE id IN (
            SELECT MAX(id) FROM thumbs_votes_old
            GROUP BY session_uuid, question
        )
        """
    )
    conn.execute("DROP TABLE thumbs_votes_old")


def save_thumbs_vote_db(vote_data, session_uuid, user_agent):
    """Enregistre (ou met à jour) un vote utilisateur dans SQLite.

    Si l'utilisateur a déjà voté pour cette question (même session_uuid),
    le vote précédent est remplacé.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO thumbs_votes (
                created_at, session_uuid, question, vote,
                validation, source, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_uuid, question) DO UPDATE SET
                created_at = excluded.created_at,
                vote       = excluded.vote,
                validation = excluded.validation,
                source     = excluded.source,
                user_agent = excluded.user_agent
            """,
            (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                session_uuid,
                vote_data['question'],
                vote_data['vote'],
                vote_data.get('validation'),
                vote_data.get('source'),
                user_agent,
            ),
        )
        conn.commit()


def get_thumbs_votes(limit=None, offset=0):
    """Retourne les votes utilisateur, du plus récent au plus ancien."""
    query = """
        SELECT id, created_at, session_uuid, question, vote,
               validation, source, user_agent
        FROM thumbs_votes
        ORDER BY id DESC
    """
    params = []

    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params = [int(limit), int(offset)]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def count_thumbs_votes():
    """Retourne le nombre total de votes enregistrés."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM thumbs_votes").fetchone()[0]


# ============================================================================
# VALIDATION DES ENTRÉES
# ============================================================================

def _clean_str(value, max_len):
    """Convertit en str, strip, et tronque à max_len."""
    return str(value or '').strip()[:max_len]


def validate_thumbs_vote(data):
    """Valide les données d'un vote (thumbs up/down).

    Lève ValueError si invalide. Retourne un dict propre sinon.
    """
    if not isinstance(data, dict):
        raise ValueError("Format JSON invalide.")

    question = _clean_str(data.get('question'), MAX_QUESTION_LEN)
    vote = _clean_str(data.get('vote'), 10).lower()

    if not question:
        raise ValueError("Le champ 'question' est requis.")
    if vote not in ALLOWED_VOTES:
        raise ValueError(f"Le champ 'vote' doit être l'un de {sorted(ALLOWED_VOTES)}.")

    return {
        'question': question,
        'vote': vote,
        'validation': _clean_str(data.get('validation'), 50),
        'source': _clean_str(data.get('source'), 100),
    }


def validate_feedback(data):
    """Valide les données d'un feedback détaillé."""
    if not isinstance(data, dict):
        raise ValueError("Format JSON invalide.")

    question = _clean_str(data.get('question'), MAX_QUESTION_LEN)
    original = _clean_str(data.get('originalResponse'), MAX_TEXT_LEN)
    fb_type = _clean_str(data.get('feedbackType'), 20).lower()

    if not question:
        raise ValueError("Le champ 'question' est requis.")
    if not original:
        raise ValueError("Le champ 'originalResponse' est requis.")
    if fb_type not in ALLOWED_FEEDBACK_TYPES:
        raise ValueError(
            f"Le champ 'feedbackType' doit être l'un de {sorted(ALLOWED_FEEDBACK_TYPES)}."
        )

    return {
        'question': question,
        'originalResponse': original,
        'feedbackType': fb_type,
        'comment': _clean_str(data.get('comment'), MAX_TEXT_LEN),
        'suggestedCorrection': _clean_str(data.get('suggestedCorrection'), MAX_TEXT_LEN),
    }


# ============================================================================
# AUTHENTIFICATION ADMIN (par session)
# ============================================================================

def require_admin(view_func):
    """Décorateur protégeant une route admin.

    Redirige vers /admin/login si l'utilisateur n'est pas connecté.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapper


# ============================================================================
# UTILITAIRES MÉTIER
# ============================================================================

def WriteTxt(prompt, name):
    """Écrit un fichier texte (utilitaire de debug)."""
    with open(f'{name}.txt', 'w', encoding='UTF-8') as file:
        file.write(prompt)


def ExtensionRight(file_name):
    """Vérifie si l'extension du fichier est autorisée."""
    _, ext = os.path.splitext(file_name)
    return ext.lower() in EXTENSIONS


def delDocument(liste_fichier):
    """Supprime les fichiers uploadés du dossier ./uploads."""
    for fichiers in liste_fichier:
        for chemin in fichiers.GetChemin():
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], chemin))
            except OSError as exc:
                print(f"Suppression impossible ({chemin}) : {exc}")


def writeJson(data):
    """Sauvegarde les réponses LLM dans un JSON horodaté."""
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    filename = f"{JSON_OUTPUT_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def creerListeFichier():
    """Initialise la liste typée des documents acceptés en upload."""
    return [
        Document('F1'),
        Document('FIC'),
        Document('outilsRecrutement'),
        Document('financement'),
        Document('rechercheMilieu'),
        Document('questionnaires'),
        Document('guideEntrevue'),
        Document('guideDiscussions'),
        Document('guideObservation'),
        Document('instrumentsMesure'),
        Document('autorisationDonneesSecondaires'),
        Document('descriptionCollecte'),
        Document('preuveCGRB'),
    ]


def UploadDesFichiers(files):
    """Sauvegarde les fichiers reçus et retourne (chemins, contenus textuels)."""
    chemins = []
    texte = []
    for file in files:
        if ExtensionRight(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            chemins.append(filename)
            texte.append(PdfOrDocx(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
    return chemins, texte


def CheckQuestion(question):
    """Envoie le prompt au LLM, parse la réponse et l'attache à la question."""
    reponse = None

    for tentative in range(2):
        try:
            reponse_raw = requetGrok405B(question.PromptGen())
            reponse = stringToJson(reponse_raw)
            break
        except Exception as exc:
            msg = str(exc)
            print(f"Erreur CheckQuestion (tentative {tentative + 1}) : {msg}")

            if "413" in msg or "rate_limit" in msg or "Insufficient credits" in msg:
                reponse = {
                    "Reponse": None,
                    "Justification": "Erreur Groq : limite de tokens dépassée ou crédit insuffisant.",
                    "Recommandation": "Réduire la taille des extraits ou attendre le reset de l'API.",
                    "Source": "N/A",
                }
                break

            time.sleep(2 * (tentative + 1))

    if reponse is None:
        reponse = {
            "Reponse": None,
            "Justification": "Une erreur est survenue lors du traitement de cette question.",
            "Recommandation": "",
            "Source": "N/A",
        }

    question.SetValide(reponse.get("Reponse"))
    question.SetReponse(reponse)


def normalize_llm_fields(data):
    """Garde-fous sur les champs renvoyés par le LLM."""
    if not isinstance(data, dict):
        return data

    response_value = data.get("Reponse")
    source = str(data.get("Source", "") or "").strip()
    recommendation = str(data.get("Recommandation", "") or "").strip()
    justification = str(data.get("Justification", "") or "").strip()

    if not source:
        data["Source"] = "N/A"

    if response_value in (True, None):
        data["Recommandation"] = ""
    elif response_value is False and not recommendation:
        data["Recommandation"] = (
            "Clarifier les informations pertinentes dans les documents du projet "
            "et ajouter les précisions nécessaires pour justifier clairement la "
            "conformité éthique."
        )

    if not justification:
        data["Justification"] = "Aucune justification exploitable n'a été fournie par le modèle."

    return data


def stringToJson(reponse):
    """Extraction robuste du JSON renvoyé par le LLM, ne crash jamais."""
    DEFAULT = {
        "Reponse": None,
        "Justification": "Aucun JSON détecté dans la réponse du modèle.",
        "Recommandation": "",
        "Source": "",
    }

    try:
        if not reponse:
            return DEFAULT

        texte = str(reponse)
        texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL | re.IGNORECASE)
        texte = re.sub(r"```(?:json)?", "", texte, flags=re.IGNORECASE)
        texte = texte.replace("```", "").replace("\ufeff", "").strip()

        start = texte.find("{")
        end = texte.rfind("}")
        if start == -1 or end == -1 or end <= start:
            print("Aucun JSON détecté dans la réponse du modèle.")
            return DEFAULT

        data = json.loads(texte[start:end + 1])
        if not isinstance(data, dict):
            return DEFAULT

        for key in ("Reponse", "Justification", "Recommandation", "Source"):
            data.setdefault(key, "" if key != "Reponse" else None)

        return normalize_llm_fields(data)

    except Exception as exc:
        print(f"Erreur parsing JSON : {exc}")
        return DEFAULT


# ============================================================================
# APPLICATION FLASK
# ============================================================================

app = Flask(__name__)

# Clé secrète : lue depuis l'environnement ou générée aléatoirement.
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = SESSION_DIR
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

Session(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
init_db()


# ----------------------------------------------------------------------------
# Hooks de session
# ----------------------------------------------------------------------------

@app.before_request
def init_progress():
    """Garantit que chaque session a un UUID et un slot de progression."""
    if 'UUID' not in session:
        session["UUID"] = str(uuid4())

    if session["UUID"] not in progress_store:
        progress_store[session["UUID"]] = {"total": 0, "current": 0}


# ----------------------------------------------------------------------------
# Routes principales
# ----------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    """Page d'accueil et endpoint de soumission de l'analyse."""
    liste_fichier = creerListeFichier()

    if request.method == 'POST':
        try:
            for fichier in liste_fichier:
                files = request.files.getlist(str(fichier))
                chemins, texte = UploadDesFichiers(files)
                fichier.SetChemin(chemins)
                fichier.SetTexte(texte)

            liste_question = UpdateObjetQuestion(CreerObjetQuestion(), liste_fichier)
            progress_store[session["UUID"]]["total"] = len(liste_question)

            for question in liste_question:
                CheckQuestion(question)
                progress_store[session["UUID"]]["current"] += 1

            json_file = [
                {"question": str(q), "reponse": q.getReponse()}
                for q in liste_question
            ]
            session['JSON'] = json_file
            writeJson(json_file)

        except Exception as exc:
            print(f"Erreur de traitement : {exc}")
        finally:
            delDocument(liste_fichier)
            progress_store.pop(session["UUID"], None)

        return render_template('resultat.html')

    return render_template('index.html')


@app.route('/give_json')
def giveJson():
    """Retourne le JSON des réponses pour la session courante."""
    return jsonify(session.get('JSON', []))


@app.route('/progress')
def get_progress():
    """Retourne l'avancement du traitement en cours."""
    data = progress_store.get(session['UUID'])
    if data is None:
        data = {"total": 1, "current": 1, "done": True}
    return jsonify(data)


# ----------------------------------------------------------------------------
# Routes de feedback / vote utilisateur
# ----------------------------------------------------------------------------

@app.route('/save_thumbs_vote_db', methods=['POST'])
def save_thumbs_vote_db_route():
    """Enregistre un vote 'correcte / incorrecte' dans SQLite."""
    try:
        validated = validate_thumbs_vote(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    try:
        save_thumbs_vote_db(
            vote_data=validated,
            session_uuid=session.get("UUID"),
            user_agent=request.headers.get('User-Agent', 'unknown'),
        )
        return jsonify({"success": True, "message": "Vote enregistré."}), 200
    except Exception as exc:
        print(f"Erreur enregistrement vote : {exc}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    """Enregistre un feedback utilisateur détaillé dans un fichier JSON quotidien."""
    try:
        validated = validate_feedback(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    try:
        feedback = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **validated,
        }

        feedback_file = (
            f"{JSON_OUTPUT_DIR}/feedback_{datetime.now().strftime('%Y%m%d')}.json"
        )

        feedbacks = []
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)

        feedbacks.append(feedback)

        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=4)

        return jsonify({"success": True, "message": "Feedback enregistré."}), 200
    except Exception as exc:
        print(f"Erreur feedback : {exc}")
        return jsonify({"success": False, "message": "Erreur serveur."}), 500


# ----------------------------------------------------------------------------
# Routes admin (login + protégées)
# ----------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion admin."""
    error = None
    next_url = request.args.get('next', url_for('thumbs_votes_admin'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        expected = os.getenv("ADMIN_TOKEN")

        if not expected:
            error = "L'accès admin n'est pas configuré (ADMIN_TOKEN manquant dans .env)."
        elif password == expected:
            session['is_admin'] = True
            # On redirige vers la page demandée à l'origine, mais en restant
            # sur le domaine local pour éviter une redirection ouverte.
            target = request.form.get('next', next_url)
            if target.startswith('/'):
                return redirect(target)
            return redirect(url_for('thumbs_votes_admin'))
        else:
            error = "Mot de passe incorrect."

    return render_template('admin_login.html', error=error, next=next_url)


@app.route('/admin/logout')
def admin_logout():
    """Déconnexion admin."""
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/thumbs-votes')
@require_admin
def thumbs_votes_admin():
    """Affiche les votes enregistrés (paginé)."""
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(200, max(10, int(request.args.get('per_page', 50))))
    except ValueError:
        page, per_page = 1, 50

    offset = (page - 1) * per_page
    votes = get_thumbs_votes(limit=per_page, offset=offset)
    total_votes = count_thumbs_votes()

    # Stats globales (sur tous les votes, pas seulement la page courante)
    with sqlite3.connect(DB_PATH) as conn:
        positive_votes = conn.execute(
            "SELECT COUNT(*) FROM thumbs_votes WHERE vote='up'"
        ).fetchone()[0]
        negative_votes = conn.execute(
            "SELECT COUNT(*) FROM thumbs_votes WHERE vote='down'"
        ).fetchone()[0]

    return render_template(
        'admin_votes.html',
        votes=votes,
        total_votes=total_votes,
        positive_votes=positive_votes,
        negative_votes=negative_votes,
        page=page,
        per_page=per_page,
    )


@app.route('/admin/thumbs-votes/export')
@require_admin
def export_thumbs_votes():
    """Exporte tous les votes en CSV."""
    votes = get_thumbs_votes()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'id', 'created_at', 'session_uuid', 'question',
        'vote', 'validation', 'source', 'user_agent',
    ])
    for v in votes:
        writer.writerow([
            v.get('id'),
            v.get('created_at'),
            v.get('session_uuid'),
            v.get('question'),
            v.get('vote'),
            v.get('validation'),
            v.get('source'),
            v.get('user_agent'),
        ])

    csv_content = output.getvalue()
    output.close()

    filename = f'thumbs_votes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return Response(
        csv_content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, threaded=True)