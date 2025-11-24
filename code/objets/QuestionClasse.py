from RAG.embeding import getSegment
from objets.DocumentClasse import Document


class Question():
    """Cette classe représente les questions demandés par le conseil d'éthique de l'UQAC"""
    def __init__(self, question : str, documents : list):
        self._question = question
        self._documents = documents

    def __repr__(self) -> str:
        """Permet de redéfinir un nom pour l'objet."""
        return self._question

    def GetDocuments(self) -> list[Document]:
        """Permet d'obtenir la liste de document."""
        return self._documents   
    
    def SetDocument(self, listenouv : list[Document]):
        """Permet d'initialisé une nouvelle liste de document."""
        self._documents = listenouv 
    
    def SetReponse(self, contenu : str):
        """Permet d'initialiser une réponse pour la Question."""
        self._reponse = contenu
    
    def SetValide(self, check : bool):
        """Permet de mettre si la réponse a été répondue positivement ou non."""
        self._valide = check
        
    def GetValide(self) -> bool:
        """Peremt d'obtenir la validation."""
        return self._valide
    
    def getReponse(self) -> str:
        """Permet d'obtenir la réponse."""
        return self._reponse
    
    def PromptGen(self) -> str:
        """Permet de généré le prompt donner au LLM"""
        texteChemin = ''
        for document in self._documents:
            for x in range(len(document.GetChemin())):
                texteChemin += f' LE DOCUMENT {document} ({document.GetChemin()[x]}) COMMENCE ICI {document.GetTexte()[x]} LE DOCUMENT {document} ({document.GetChemin()[x]}) FINI ICI ' 

        ragSegment1, ragSegment2, ragSegment3, ragSegment4, ragSegment5 = getSegment(self._question)
        
            
        prompt = f"""Tu es un expert dans l'évaluation des demandes d'approbation
            pour le comité d'éthique à la recherche de l'Université du Québec à Chicoutimi.
            Ton rôle est de faire une évaluation rigoureuse des enjeux éthiques entourant
            la recherche impliquant des participants humains.

            Tu dois répondre à la question d'évaluation par rapport à un dossier déposé.
            - Si le dossier répond positivement à la question, explique ton raisonnement
            et justifie pourquoi les documents sont conformes.
            - Si le dossier ne répond pas à la question, formule une rétroaction claire
            et actionnable pour que le chercheur puisse corriger les documents.
            - Si le dossier ne répond pas à la question parce qu'elle ne s'applique pas
            au projet de recherche, explique ton raisonnement
            et justifie pourquoi les documents montrent que la question ne
            concerne pas le projet de recherche.

            
            Dans les trois cas, commence obligatoirement ta réponse par un "Oui", "Non" ou "Ne s'applique pas" clair. Ta réposne doit exclusivement
            contenir du texte en FRANÇAIS. Exemples : "Non. La...", "Oui." ou "Ne s'applique pas.". 
            Le Non., le Oui. et le Ne s'applique pas ne doivent pas être entouré de carcatere spéciaux ou de saut 
            de ligne ou autre Le dossier...". Formate ton texte d'une manière simple sans superflu. 
            Le texte ne doit pas contenir de gras, d'italic etc. 

            La question à évaluer est : {self._question}

            Pour y répondre, tu devras consulter ces documents : {texteChemin}

            Voici un extrait d'information supplémentaire issu de la recherche (RAG) :
            - Chunk 1 : {ragSegment1.page_content}
            - Chunk 2 : {ragSegment2.page_content}
            - Chunk 3 : {ragSegment3.page_content}
            - Chunk 4 : {ragSegment4.page_content}
            - Chunk 5 : {ragSegment5.page_content}
            """ + r" \no_think"
        

        return prompt