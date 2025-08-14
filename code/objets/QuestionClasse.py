
class Question():

    def __init__(self, question : str, documents : list):
        self._question = question
        self._documents = documents

    def __repr__(self):
        return self._question

    def get_documents(self):
        return self._documents    
    
    