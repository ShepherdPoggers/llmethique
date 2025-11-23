import os
from objets.DocumentClasse import Document
from flask import Flask, request, session, render_template, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
from fonctions.fonctionsDivers import CreerObjetQuestion, UpdateObjetQuestion, PdfOrDocx
from fonctions.requetellm import requete, requetGroq, requetopenrouter
import json
from datetime import datetime
import re

EXTENSIONS = ['.pdf', '.docx']




def WriteTxt(prompt, name):
    with open(f'{name}.txt', 'w', encoding='UTF-8') as file:
        file.write(prompt)


def ExtensionRight(fileName: str) -> bool:
    """Permet de vérifier si l'extension est valide"""
    _, ext = os.path.splitext(fileName)
    return ext.lower() in EXTENSIONS

def delDocument(listeFicher):
    for fichiers in listeFicher:
        for chemin in fichiers.GetChemin():
            os.remove((app.config['UPLOAD_FOLDER'] + '/' + chemin))

def writeJson(data):
    with open(f"code/data/jsonProf/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def creerListeFichier():
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

app = Flask(__name__)
app.secret_key = 'ton_secret_unique'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = "code\data\session"
app.config['UPLOAD_FOLDER'] = 'code/uploads'

Session(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    """Permet de gérer l'upload des fichiers sur le serveur"""
    
    #Initie les types de documents pour après bien classer les fichiers lors de l'uppload
    
    listeFicher = creerListeFichier()

    if request.method == 'POST':
        try:
            for fichier in listeFicher:
                files = request.files.getlist(str(fichier)) 
                chemins = []
                texte = []
                
                for file in files:
                    if ExtensionRight(file.filename): 
                            print("Ca marche")
                            filename = secure_filename(file.filename) #Normalise les noms des documents
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #Sauvegarde dans le fichier uploads le document
                            chemins.append(filename) #Ajoute le path à une liste
                            texte.append(PdfOrDocx(app.config['UPLOAD_FOLDER'] + '/' + filename))
                fichier.SetChemin(chemins)
                fichier.SetTexte(texte)
            
            lsiteQuestion = UpdateObjetQuestion(CreerObjetQuestion(), listeFicher)
            
            session['PROGRESS'] = {"total" : len(lsiteQuestion), "current" : 0}
            
            
            for question in lsiteQuestion:
                reponse = requetopenrouter(question.PromptGen())
                if reponse[:3].lower() == 'oui':
                    question.SetValide(True)
                    
                elif reponse[:3].lower() == 'non':
                    question.SetValide(False)
                else:
                    question.SetValide(None)
                question.SetReponse(reponse)
                session["PROGRESS"]["current"] += 1

                
            jsonFile = [{"question": str(question), "reponse": question.getReponse(), "Check": question.GetValide()} for question in lsiteQuestion]    
            session['JSON'] = jsonFile
            writeJson(jsonFile)
            delDocument(listeFicher)
        except Exception as e:
            print(e)
            with open('questions_reponses.json', 'r', encoding='UTF-8') as file:
                session['JSON'] = json.load(file)
                delDocument(listeFicher)

        return render_template('resultat.html')
    
    return render_template('index.html')

@app.route("/give_json")
def giveJson():
    data = session['JSON']
    return jsonify(data)

@app.route('/progress')
def get_progress():
    data = session['PROGRESS']
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=False)
