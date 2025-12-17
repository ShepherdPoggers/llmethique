
class Document():
    """La classe document représente une catégorie de document nécéssaire pour répondre aux question du comité éthique."""
    def __init__(self, nom : str):
        """Cette fonction permet de construire l'objet de type Document"""
        self._nom = nom
        self._chemin = []
        self._texte = []
    def __repr__(self) -> str:
        """Permet de redéfinir un nom pour l'objet."""
        return self._nom

    def GetChemin(self) -> list[str]:
        """Permet d'obtenir la liste de chemin."""
        return self._chemin    
    
    def SetChemin(self, chemin : list[str]):
        """Permet de définir la liste de chemin."""
        self._chemin = chemin
        
    def SetTexte(self, texte : list[str]):
        """Peremt de définir la liste des textes fournie."""
        self._texte = texte
    
    def GetTexte(self) -> list[str]:
        """Permet d'obtenir la liste de texte"""
        return self._texte