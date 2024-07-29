import os
import uuid
import logging
from langchain_chroma import Chroma
from langchain.embeddings.base import Embeddings
import requests
from typing import List
from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, DB_STORAGE_DIR
import hashlib
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaEmbeddings(Embeddings):
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_EMBED_MODEL

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
        self.embeddings = OllamaEmbeddings()
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

    def create_index(self, chunks, source_dir, show_progress=False):
        logger.info(f"Creating index for {source_dir} with {len(chunks)} chunks")
        if not chunks:
            logger.warning(f"Received empty chunks list for {source_dir}. No index will be created.")
            return

        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Create or get the collection with our custom embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.chroma_embed_function
            )
            
            # Use tqdm for progress bar
            chunk_iterator = tqdm(chunks, desc=f"Indexing chunks for {source_dir}", disable=not show_progress)
            for chunk in chunk_iterator:
                if chunk.metadata['source'] not in self.processed_files:
                    self._add_chunk_to_collection(chunk, source_dir)
                    self.processed_files.add(chunk.metadata['source'])
                    self._update_cache_file(chunk.metadata['source'], source_dir)
            
            logger.info(f"Index created and persisted successfully for {source_dir} at {self.persist_directory}")
            
            # Create Langchain's Chroma wrapper
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
        except Exception as e:
            logger.error(f"An error occurred while creating the index for {source_dir}: {str(e)}")
            raise Exception(f"An error occurred while creating the index for {source_dir}: {str(e)}")

    def update_index(self, new_chunks, source_dir):
        logger.info(f"Updating index for {source_dir} with {len(new_chunks)} new chunks")
        if not new_chunks:
            logger.warning(f"Received empty new_chunks list for {source_dir}. No update will be performed.")
            return

        if self.collection is None:
            self.create_index(new_chunks, source_dir)
        else:
            for chunk in new_chunks:
                if chunk.metadata['source'] not in self.processed_files:
                    self._add_chunk_to_collection(chunk, source_dir)
                    self.processed_files.add(chunk.metadata['source'])
                    self._update_cache_file(chunk.metadata['source'], source_dir)
            
            logger.info(f"Index updated and persisted successfully for {source_dir} at {self.persist_directory}")

    def _add_chunk_to_collection(self, chunk, source_dir):
        metadata = chunk.metadata.copy()
        metadata['source_dir'] = source_dir
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[chunk.page_content],
            metadatas=[metadata]
        )

    def _update_cache_file(self, file_path, source_dir):
        with open(self.cache_file, 'a') as f:
            file_hash = self.get_file_hash(file_path)
            f.write(f"{source_dir}:{file_path}:{file_hash}\n")

    def search(self, query, source_dir=None, k=4):
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
        
        if source_dir:
            filter_dict = {"source_dir": source_dir}
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            return self.vector_store.similarity_search(query, k=k)

    def cache_document_hashes(self, files, source_dir):
        with open(self.cache_file, 'a') as f:
            for file_path in files:
                file_hash = self.get_file_hash(file_path)
                f.write(f"{source_dir}:{file_path}:{file_hash}\n")

    def get_file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def check_for_changes(self, files, source_dir):
        if not os.path.exists(self.cache_file):
            return True  # No cache file, assume changes

        current_hashes = {file_path: self.get_file_hash(file_path) for file_path in files}
        
        with open(self.cache_file, 'r') as f:
            cached_hashes = {}
            for line in f:
                parts = line.strip().split(':')
                if len(parts) == 3:
                    cached_source_dir, file_path, file_hash = parts
                    if cached_source_dir == source_dir:
                        cached_hashes[file_path] = file_hash

        self.processed_files.update(cached_hashes.keys())
        
        return any(
            file_path not in cached_hashes or
            current_hashes[file_path] != cached_hashes[file_path]
            for file_path in current_hashes
        )