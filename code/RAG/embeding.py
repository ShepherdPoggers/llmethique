from split import chunckSplit
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def  embeding():
    paragraphe = chunckSplit(r'code\RAG\tcps2-2022-fr-pageutile.pdf')
    embed = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    encode_kwargs={"normalize_embeddings": True},  # cos-sim plus stable
    )
    vs = FAISS.from_documents(paragraphe, embedding=embed)
    vs.save_local("index_faiss_tcps2")
    
embeding()
print('Done')