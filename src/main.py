import os
from includes.objets.DocumentClasse import Document
from flask import Flask, request, session, render_template, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
from includes.fonctions.divers import CreerObjetQuestion, UpdateObjetQuestion, PdfOrDocx
from includes.fonctions.requetellm import requete, requetGrok, requetopenrouter
import json
from datetime import datetime
import re
from uuid import uuid4


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
    
    for x in range(5): #On essaie 5 fois sinon on met qu'il y a eu une erreur du traitement
        try:
            reponse = requetopenrouter(question.PromptGen())
            reponseClean = re.sub(r"<think>.*?</think>", "", reponse, flags=re.DOTALL)
            reponse = stringToJson(reponseClean)
            break  
        except Exception as e:
            print(e)
            continue 
    else:
        reponse = {
            "Reponse": None,
            "Justification": "Une erreur est survenu lors du traitement de cette question."
        }
        
    question.SetValide(reponse["Reponse"])
    question.SetReponse(reponse)


def stringToJson(reponse):
    
    match = re.search(r"\{[\s\S]*\}", reponse)
    json_str = match.group()
    data = json.loads(json_str)
    

    return data

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



@app.route("/give_json")
def giveJson():
    """Permet de retourner le json des reponse"""
    data = session['JSON']
    
    return jsonify(data)

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


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
