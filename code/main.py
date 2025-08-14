import os
from flask import Flask, render_template, request, session, jsonify, send_from_directory, flash


EXTENSIONS = ['.pdf', '.docx']


def ExtensionRight(fileName: str) -> bool:
    """Permet de vérifier si l'extension est valide"""
    return fileName[-4:] in EXTENSIONS

app = Flask(__name__)
app.secret_key = 'ton_secret_unique'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['']

@app.route('/', methods=['GET', 'POST'])
def UploadFile():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("N'y a pas de fichier :(")



@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    app.run(debug=False)