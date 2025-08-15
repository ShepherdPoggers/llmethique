import os
from objets.DocumentClasse import Document
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

EXTENSIONS = ['.pdf', '.docx']


def ExtensionRight(fileName: str) -> bool:
    """Permet de vérifier si l'extension est valide"""
    _, ext = os.path.splitext(fileName)
    return ext.lower() in EXTENSIONS

app = Flask(__name__)
app.secret_key = 'ton_secret_unique'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'code\\uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    listeDocument = []
    if request.method == 'POST':
        files = request.files.getlist('fichier1') 
        
        tempLISt = [
            Document(file.filename, 'uploads' + "\\" + file.filename)
            for file in files
            if ExtensionRight(file.filename)
        ]
        
        for file in files:
            if ExtensionRight(file.filename):
                    print("Ca marche")
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    fileGood.append(Document(filename, 'uploads' + "\\" + filename))
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=False)