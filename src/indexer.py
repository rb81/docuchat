import os
import uuid
import logging
from langchain_chroma import Chroma
from langchain.embeddings.base import Embeddings
import requests
from typing import List
from config import OLLAMA_BASE_URL, DB_STORAGE_DIR
import hashlib
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Disable Chroma telemetry and import PersistentClient
import chromadb
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction

class OllamaEmbeddings(Embeddings):
    def __init__(self, base_url: str, model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            embeddings.append(response.json()['embedding'])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, ollama_embeddings: OllamaEmbeddings):
        self.ollama_embeddings = ollama_embeddings

    def __call__(self, texts: Documents) -> List[List[float]]:
        return self.ollama_embeddings.embed_documents(texts)

class Indexer:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL)
        self.persist_directory = os.path.join(DB_STORAGE_DIR, 'chroma_db')
        self.cache_file = os.path.join(DB_STORAGE_DIR, 'document_cache.txt')
        self.chroma_settings = Settings(
            anonymized_telemetry=False,
            is_persistent=True
        )
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory, settings=self.chroma_settings)
        self.collection_name = "document_collection"
        self.collection = None
        self.vector_store = None

        # Create a ChromaDB embedding function that wraps our OllamaEmbeddings
        self.chroma_embed_function = OllamaEmbeddingFunction(self.embeddings)

        # Initialize set to keep track of processed files
        self.processed_files = set()

    def create_index(self, chunks, show_progress=False):
        logger.info(f"Creating index with {len(chunks)} chunks")
        if not chunks:
            logger.warning("Received empty chunks list. No index will be created.")
            return

        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Create or get the collection with our custom embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.chroma_embed_function
            )
            
            # Use tqdm for progress bar
            chunk_iterator = tqdm(chunks, desc="Indexing chunks", disable=not show_progress)
            for chunk in chunk_iterator:
                if chunk.metadata['source'] not in self.processed_files:
                    self._add_chunk_to_collection(chunk)
                    self.processed_files.add(chunk.metadata['source'])
                    self._update_cache_file(chunk.metadata['source'])
            
            logger.info(f"Index created and persisted successfully at {self.persist_directory}")
            
            # Create Langchain's Chroma wrapper
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
        except Exception as e:
            logger.error(f"An error occurred while creating the index: {str(e)}")
            raise Exception(f"An error occurred while creating the index: {str(e)}")

    def update_index(self, new_chunks):
        logger.info(f"Updating index with {len(new_chunks)} new chunks")
        if not new_chunks:
            logger.warning("Received empty new_chunks list. No update will be performed.")
            return

        if self.collection is None:
            self.create_index(new_chunks)
        else:
            for chunk in new_chunks:
                if chunk.metadata['source'] not in self.processed_files:
                    self._add_chunk_to_collection(chunk)
                    self.processed_files.add(chunk.metadata['source'])
                    self._update_cache_file(chunk.metadata['source'])
            
            logger.info(f"Index updated and persisted successfully at {self.persist_directory}")

    def _add_chunk_to_collection(self, chunk):
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[chunk.page_content],
            metadatas=[chunk.metadata]
        )

    def _update_cache_file(self, file_path):
        with open(self.cache_file, 'a') as f:
            file_hash = self.get_file_hash(file_path)
            f.write(f"{file_path}:{file_hash}\n")

    def search(self, query, k=4):
        if self.vector_store is None:
            if os.path.exists(self.persist_directory):
                logger.info(f"Loading existing Chroma index from {self.persist_directory}")
                self.chroma_client = chromadb.PersistentClient(path=self.persist_directory, settings=self.chroma_settings)
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.chroma_embed_function
                )
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
            else:
                logger.error("Index has not been created yet")
                raise ValueError("Index has not been created yet.")
        logger.info(f"Performing similarity search for query: {query}")
        return self.vector_store.similarity_search(query, k=k)

    def cache_document_hashes(self, files):
        with open(self.cache_file, 'w') as f:
            for file_path in files:
                file_hash = self.get_file_hash(file_path)
                f.write(f"{file_path}:{file_hash}\n")

    def get_file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def check_for_changes(self, files):
        if not os.path.exists(self.cache_file):
            return True  # No cache file, assume changes

        current_hashes = {file_path: self.get_file_hash(file_path) for file_path in files}
        
        with open(self.cache_file, 'r') as f:
            cached_hashes = dict(line.strip().split(':') for line in f)

        self.processed_files = set(cached_hashes.keys())
        
        return any(
            file_path not in cached_hashes or
            current_hashes[file_path] != cached_hashes[file_path]
            for file_path in current_hashes
        )