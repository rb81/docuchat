import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def load_document(file_path):
    logger.info(f"Loading document: {file_path}")
    try:
        if file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.lower().endswith('.txt'):
            loader = TextLoader(file_path)
        elif file_path.lower().endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return []
        
        docs = loader.load()
        logger.info(f"Successfully loaded {len(docs)} pages/sections from {file_path}")
        return docs
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {str(e)}")
        return []

def process_documents(files, show_progress=False):
    logger.info(f"Processing {len(files)} files")
    documents = []
    file_iterator = tqdm(files, desc="Processing files", disable=not show_progress)
    for file in file_iterator:
        docs = load_document(file)
        documents.extend(docs)
    
    logger.info(f"Total documents loaded: {len(documents)}")
    
    if not documents:
        logger.warning("No documents were successfully loaded. Returning empty list of chunks.")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    
    logger.info(f"Created {len(chunks)} chunks from the documents")

    for i, chunk in enumerate(chunks):
        if 'page' in chunk.metadata:
            chunk.metadata['page'] = str(int(chunk.metadata['page']) + 1)
        else:
            chunk.metadata['page'] = str(i + 1)
    
    return chunks