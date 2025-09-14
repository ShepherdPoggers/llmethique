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
    
    def get_reponse(self):
        return self._reponse
    
    def PromptGen(self):
        
        texteChemin = ''
        for document in self._documents:
            for x in range(len(document.GetChemin())):
                texteChemin += f' LE DOCUMENT {document} ({document.GetChemin()[x]}) COMMENCE ICI {document.GetTexte()[x]} LE DOCUMENT {document} ({document.GetChemin()[x]}) FINI ICI ' 

        ragSegment1, ragSegment2, ragSegment3, ragSegment4, ragSegment5 = getSegment(self._question)
        
            
        prompt = f"Tu es un expert dans l'évaluation de demande d'approbation pour "\
        "le comité d'éthique à la recherche de l'Université du Québec à Chicoutimi." \
        "Ton rôle est de faire une évaluation rigoureuse des questions éthiques entourrant" \
        "la recherche impliquant des participants humains. Tu dois répondre à cette question" \
        "d'évaluation par rapport à un dossier déposé. Dans le cas où le dossier répondrait" \
        "positivement à la quesiton, écris une simple phrase qui précise que la question est bien répondu."\
        "Dans le cas où le dossier ne répond pas à la question," \
        "assure-toi de formuler une rétroaction claire et actionnable pour que le chercheur puisse" \
        f"aisament corriger les différents documents \n La question à évaluer est : {self._question}" \
        f"Pour y répondre tu devras consulter ces documents : {texteChemin}" \
        f"Voici un extrait d'information supplémentaire issu de la recherche (RAG) : Chunk 1 {ragSegment1.page_content}, Chunk 2 {ragSegment2.page_content}, Chunk 3 {ragSegment3.page_content}, Chunk 4 {ragSegment4.page_content}, Chunk 5{ragSegment5.page_content}"
        return prompt