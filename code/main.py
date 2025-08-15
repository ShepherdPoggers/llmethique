import os
from objets.DocumentClasse import Document
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

EXTENSIONS = ['.pdf', '.docx']




def ExtensionRight(fileName: str) -> bool:
    """Permet de vérifier si l'extension est valide"""
    _, ext = os.path.splitext(fileName)
    return ext.lower() in EXTENSIONS

def delDocument(listeFicher):
    for fichiers in listeFicher:
        for chemin in fichiers.getChemin():
            os.remove((chemin))

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
    Document('FDC'),
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
            
            for file in files:
                if ExtensionRight(file.filename): 
                        print("Ca marche")
                        filename = secure_filename(file.filename) #Normalise les noms des documents
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #Sauvegarde dans le fichier uploads le document
                        chemins.append(app.config['UPLOAD_FOLDER'] + '\\' + filename) #Ajoute le path à une liste
            fichier.setChemin(chemins)
    delDocument(listeFicher)
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=False)