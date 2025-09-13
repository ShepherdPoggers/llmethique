from RAG.split import chunckSplit
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def  embeding():
    paragraphe = chunckSplit(r'code\RAG\tcps2-2022-fr-pageutile.pdf')
    embed = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    encode_kwargs={"normalize_embeddings": True},  # cos-sim plus stable
    )
    vs = FAISS.from_documents(paragraphe, embedding=embed)
    vs.save_local("index_faiss_tcps2")
    
def getSegment(question):
    embed = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    encode_kwargs={"normalize_embeddings": True}
)
    vs = FAISS.load_local(
        "index_faiss_tcps2",
        embeddings=embed,
        allow_dangerous_deserialization=True  # nécessaire avec LangChain >=0.2
    )
    
    results = vs.similarity_search(question, k=5)
    return results
