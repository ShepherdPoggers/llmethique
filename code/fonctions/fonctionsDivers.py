import json
from objets.QuestionClasse import Question

def CreerObjetQuestion(path=r"code\data\questions.json") -> list:
    listeQuestions = []
    with open(path, "r", encoding="UTF-8") as file:
        
        data = json.load(file)
        
    for dict in data:
        listeQuestions.append(Question(dict["question"], dict["documents"]))
    
    return listeQuestions


def UpdateObjetQuestion(questions: list, documents: list):
    # Création d'un dictionnaire de lookup : str(document) -> objet document
    documents_dict = {str(document): document for document in documents}
    
    for question in questions:
        # On remplace les strings par les vrais objets document correspondants
        listnouv = [
            documents_dict[docQ]
            for docQ in question.get_documents()
            if docQ in documents_dict
        ]
        question.set_document(listnouv)
    return questions

        
    