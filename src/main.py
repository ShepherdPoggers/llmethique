import os
from dotenv import load_dotenv
from includes.objets.DocumentClasse import Document
from flask import Flask, request, session, render_template, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
from includes.fonctions.divers import CreerObjetQuestion, UpdateObjetQuestion, PdfOrDocx
from includes.fonctions.requetellm import requete, requetGrok, requetGrok405B
import json
from datetime import datetime
import re
import time
from uuid import uuid4

# Charger les variables d'environnement depuis .env
load_dotenv()


EXTENSIONS = ['.pdf', '.docx']

progress_store = {}  


def WriteTxt(prompt, name):
    """Permet d'écrire un fichier txt."""
    with open(f'{name}.txt', 'w', encoding='UTF-8') as file:
        file.write(prompt)


def ExtensionRight(fileName: str) -> bool:
    """Permet de vérifier si l'extension est valide"""
    _, ext = os.path.splitext(fileName)
    return ext.lower() in EXTENSIONS

def delDocument(listeFicher):
    """Permet de supprimé une liste de fichier du fichier ./uploads"""
    for fichiers in listeFicher:
        for chemin in fichiers.GetChemin():
            os.remove((app.config['UPLOAD_FOLDER'] + '/' + chemin))

def writeJson(data):
    """Permet d'écrire des données dans un fichier JSON"""
    with open(f"src/data/jsonProf/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def creerListeFichier():
    """Initie les types de documents pour après bien classer les fichiers lors de l'uppload"""
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
    Document('preuveCGRB')
]

def UploadDesFichiers(files):
    """Permet de creer deux liste, une pour le contenue et l'autre pour les chemis d'upload"""
    chemins = []
    texte = []
    for file in files:
        if ExtensionRight(file.filename): 
            filename = secure_filename(file.filename) #Normalise les noms des documents
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #Sauvegarde dans le fichier uploads le document
            chemins.append(filename) #Ajoute le path à une liste
            texte.append(PdfOrDocx(app.config['UPLOAD_FOLDER'] + '/' + filename))
    return chemins, texte

def CheckQuestion(question):
    """Permet d'envoyer le prompt et de valider la reponse"""
    
    for x in range(2):
        try:
            reponse_raw = requetGrok405B(question.PromptGen())
            data = stringToJson(reponse_raw)
            reponse = data
            break
        except Exception as e:
            msg = str(e)
            print("Erreur CheckQuestion:", msg)

            # Si crédits insuffisants ou tokens dépassés -> on stoppe
            if "413" in msg or "rate_limit" in msg or "Insufficient credits" in msg:
                reponse = {
                    "Reponse": None,
                    "Justification": "Erreur Groq : limite de tokens dépassée ou crédit insuffisant.",
                    "Recommandation": "Réduire la taille des extraits ou attendre le reset de l'API."
                }
                break

            time.sleep(2 * (x + 1))
            continue
    else:
        reponse = {
            "Reponse": None,
            "Justification": "Une erreur est survenu lors du traitement de cette question.",
            "Recommandation": ""
        }

    question.SetValide(reponse.get("Reponse"))
    question.SetReponse(reponse)


def normalize_llm_fields(data):
    """Applique des garde-fous simples sur les champs de sortie du LLM."""
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
            "Clarifier les informations pertinentes dans les documents du projet et ajouter les precisions "
            "necessaires pour justifier clairement la conformite ethique."
        )

    if not justification:
        data["Justification"] = "Aucune justification exploitable n'a ete fournie par le modele."

    return data


def stringToJson(reponse):
    """
    Extraction robuste du JSON renvoyé par le LLM.
    Ne crash jamais.
    Retourne un dictionnaire par défaut si problème.
    """

    DEFAULT = {
        "Reponse": None,
        "Justification": "Aucun JSON détecté dans la réponse du modèle.",
        "Recommandation": "",
        "Source": ""
    }

    try:
        if not reponse:
            return DEFAULT

        # Nettoyage basique
        texte = str(reponse)

        # Retire balises <think>...</think>
        texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL | re.IGNORECASE)

        # Retire blocs ```json ``` éventuels
        texte = re.sub(r"```(?:json)?", "", texte, flags=re.IGNORECASE)
        texte = texte.replace("```", "")

        # Supprime caractères invisibles
        texte = texte.replace("\ufeff", "").strip()

        # Extraction entre première { et dernière }
        start = texte.find("{")
        end = texte.rfind("}")

        if start == -1 or end == -1 or end <= start:
            print("Aucun JSON détecté")
            return DEFAULT

        json_str = texte[start:end+1]

        data = json.loads(json_str)

        # Sécurise les clés attendues
        if not isinstance(data, dict):
            return DEFAULT

        data.setdefault("Reponse", None)
        data.setdefault("Justification", "")
        data.setdefault("Recommandation", "")
        data.setdefault("Source", "")

        return normalize_llm_fields(data)

    except Exception as e:
        print("Erreur parsing JSON :", e)
        return DEFAULT

app = Flask(__name__) #initiation de l'app flask
app.secret_key = 'ton_secret_unique'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = "src/data/session"
app.config['UPLOAD_FOLDER'] = 'src/uploads'

Session(app) 

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    """Permet de gérer l'upload des fichiers sur le serveur"""
    
    listeFicher = creerListeFichier()
    if request.method == 'POST':
        try:
            for fichier in listeFicher:
                files = request.files.getlist(str(fichier)) 
                chemins, texte = UploadDesFichiers(files)
                fichier.SetChemin(chemins)
                fichier.SetTexte(texte)
            
            lsiteQuestion = UpdateObjetQuestion(CreerObjetQuestion(), listeFicher)
            progress_store[session["UUID"]]["total"] = len(lsiteQuestion)
            for question in lsiteQuestion:
                CheckQuestion(question)
                progress_store[session["UUID"]]["current"] += 1
    
            jsonFile = [{"question": str(question), "reponse": question.getReponse()} for question in lsiteQuestion]    
            session['JSON'] = jsonFile
            writeJson(jsonFile)
            delDocument(listeFicher)
        except Exception as e:
            print(e)   
            delDocument(listeFicher)
        del progress_store[session["UUID"]]
        return render_template('resultat.html')
    
    return render_template('index.html')

@app.before_request
def init_progress():
    if 'UUID' not in session:
        session["UUID"] = str(uuid4())

    # Si jamais la clé n'existe plus dans progress_store, on la recrée
    if session["UUID"] not in progress_store:
        progress_store[session["UUID"]] = {"total": 0, "current": 0}



@app.route('/give_json')
def giveJson():
    """Permet de retourner le json des reponse"""
    data = session['JSON']
    
    return jsonify(data)

@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    """Sauvegarde un feedback utilisateur sur une réponse"""
    try:
        feedback_data = request.get_json()
        
        feedback = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "question": feedback_data.get('question'),
            "originalResponse": feedback_data.get('originalResponse'),
            "feedbackType": feedback_data.get('feedbackType'),  # 'incorrect', 'incomplete', 'other'
            "comment": feedback_data.get('comment'),
            "suggestedCorrection": feedback_data.get('suggestedCorrection')
        }
        
        # Sauvegarder dans un fichier JSON
        feedback_file = f"src/data/jsonProf/feedback_{datetime.now().strftime('%Y%m%d')}.json"
        
        feedbacks = []
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        
        feedbacks.append(feedback)
        
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=4)
        
        return jsonify({"success": True, "message": "Feedback enregistré"}), 200
    except Exception as e:
        print(f"Erreur feedback: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/progress')
def get_progress():
    """Permet de retourner le progrès actuel pour le traitement des questions"""
    data = progress_store[session['UUID']]
    if data is None:
        # Soit la session est terminée, soit le traitement est fini.
        # Tu peux renvoyer un état "terminé" pour que le front arrête de poller.
        data = {"total": 1, "current": 1, "done": True}

    print(f"Reponse /progress : {data}")
    return jsonify(data)


@app.route('/save_thumbs_vote', methods=['POST'])
def save_thumbs_vote():
    """Sauvegarde un vote pouce haut/bas sur une réponse"""
    try:
        vote_data = request.get_json()
        
        vote = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "question": vote_data.get('question'),
            "vote": vote_data.get('vote'),  # 'up' ou 'down'
            "userAgent": request.headers.get('User-Agent', 'unknown')
        }
        
        # Sauvegarder dans un fichier JSON dédié
        votes_file = f"src/data/jsonProf/thumbs_votes_{datetime.now().strftime('%Y%m%d')}.json"
        
        votes = []
        if os.path.exists(votes_file):
            with open(votes_file, "r", encoding="utf-8") as f:
                votes = json.load(f)
        
        votes.append(vote)
        
        with open(votes_file, "w", encoding="utf-8") as f:
            json.dump(votes, f, ensure_ascii=False, indent=4)
        
        return jsonify({"success": True, "message": "Vote enregistré"}), 200
    except Exception as e:
        print(f"Erreur vote: {e}")
        return jsonify({"success": False, "message": str(e)}), 500





if __name__ == "__main__":
    app.run(debug=False, threaded=True)
