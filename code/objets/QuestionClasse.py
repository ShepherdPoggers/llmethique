from RAG.embeding import getSegment

class Question():

    def __init__(self, question : str, documents : list):
        self._question = question
        self._documents = documents

    def __repr__(self):
        return self._question

    def GetDocuments(self):
        return self._documents   
    
    def SetDocument(self, listenouv):
        self._documents = listenouv 
    
    def SetReponse(self, contenu):
        self._reponse = contenu
    
    def SetValide(self, check):
        self._valide = check
        
    def GetValide(self):
        return self._valide
    
    def getReponse(self):
        return self._reponse
    
    def PromptGen(self):
        
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

            Dans les deux cas, commence ta réponse par un "Oui" ou un "Non" clair.
            Exemples : "Non. La..." ou "Oui. le Non. ou le Oui. ne doit pas etre entouere de carcatere specieaux ou de saut de ligne ou autre Le dossier...".

            La question à évaluer est : {self._question}

            Pour y répondre, tu devras consulter ces documents : {texteChemin}

            Voici un extrait d'information supplémentaire issu de la recherche (RAG) :
            - Chunk 1 : {ragSegment1.page_content}
            - Chunk 2 : {ragSegment2.page_content}
            - Chunk 3 : {ragSegment3.page_content}
            - Chunk 4 : {ragSegment4.page_content}
            - Chunk 5 : {ragSegment5.page_content}
            """

        return prompt