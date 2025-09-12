
class Document():

    def __init__(self, nom):
        self._nom = nom
        self._chemin = []
        self._texte = []
    def __repr__(self):
        return self._nom

    def GetChemin(self):
        return self._chemin    
    
    def SetChemin(self, chemin : str):
        self._chemin = chemin
        
    def SetTexte(self, texte):
        self._texte = texte
    
    def GetTexte(self):
        return self._texte