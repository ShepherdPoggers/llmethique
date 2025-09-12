import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

PDF_PATH = r"code\RAG\tcps2-2022-fr-pageutile.pdf"

PAT_CHAP     = r"(?m:^\s*CHAPITRE\s+\d+\b.*$)"
PAT_INTRO    = r"(?m:^\s*INTRODUCTION\s*$)"
PAT_GLOSS    = r"(?m:^\s*GLOSSAIRE\s*$)"
PAT_SECTION  = r"(?m:^\s*[A-Z]\.\s+.+$)"    
PAT_ARTICLE  = r"(?m:^\s*Article\s+\d+\.\d+\b.*$)"

def splitInit(document):
    split1 = RecursiveCharacterTextSplitter(
        chunk_size=10**9,
        chunk_overlap=0,
        separators=[PAT_INTRO, PAT_CHAP, PAT_GLOSS, r"\Z"],
        is_separator_regex=True
    )
    split1 = split1.split_documents(document)
    return split1

def sectionSplitter(document):
    splitSection = RecursiveCharacterTextSplitter(
        chunk_size=10**9,
        chunk_overlap=0,            
        separators=[PAT_SECTION, r"\Z"],  
        is_separator_regex=True
    )
    splitSection = splitSection.split_documents(document)
    return splitSection

def articleSplitter(document):
    art_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10**9,
            chunk_overlap=0,
            separators=[PAT_ARTICLE, r"\Z"],
            is_separator_regex=True
        )
    subs = art_splitter.split_documents(document)
    return subs

def paragraphSplitter(document):
    paragraph_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=220, 
        separators=["\n\n", "\n", ". ", " "],  
        is_separator_regex=False
    )

    paragraphe = paragraph_splitter.split_documents(document)
    return paragraphe


def chunckSplit(path):
    loader = PyPDFLoader(path)
    pages = loader.load()
    paragraphe = paragraphSplitter(articleSplitter(sectionSplitter(splitInit(pages))))
    return paragraphe
