import os
from objets.DocumentClasse import Document
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from fonctions.fonctionsDivers import CreerObjetQuestion, UpdateObjetQuestion, PdfOrDocx
from fonctions.requetellm import requete
import json

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
            os.remove((app.config['UPLOAD_FOLDER'] + '\\' + chemin))

def writeJson(data):
    with open("questions_reponses.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

app = Flask(__name__)
app.secret_key = 'ton_secret_unique'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'code\\uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    """Permet de gérer l'upload des fichiers sur le serveur"""
    
    #Initie les types de documents pour après bien classer les fichiers lors de l'uppload
    
    listeFicher = [
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

    if request.method == 'POST':
       
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
                        texte.append(PdfOrDocx(app.config['UPLOAD_FOLDER'] + '\\' + filename))
            fichier.SetChemin(chemins)
            fichier.SetTexte(texte)
        lsiteQuestion = UpdateObjetQuestion(CreerObjetQuestion(), listeFicher)
        for question in lsiteQuestion:
            reponse = requete(question.PromptGen())
            question.SetReponse(reponse)
        json = [{"question": str(question), "reponse": question.getReponse()} for question in lsiteQuestion]    
        writeJson(json)
        
    delDocument(listeFicher)
    
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=False)
