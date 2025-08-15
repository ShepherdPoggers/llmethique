
class Document():

    def __init__(self, nom : str, chemin : str):
        self._nom = nom
        self._chemin = chemin

    def __repr__(self):
        return self._nom

    def getChemin(self):
        return self._chemin    
    
    def setChemin(self, chemin : str):
        self._chemin = chemin