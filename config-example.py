import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama settings
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:latest')
OLLAMA_EMBED_MODEL = os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')

# Document source directory
DOCUMENT_SOURCE_DIR = os.getenv('DOCUMENT_SOURCE_DIR', os.path.expanduser('/path/to/your/documents'))

# Database storage location
DB_STORAGE_DIR = os.getenv('DB_STORAGE_DIR', os.path.expanduser('/path/to/store/database'))

# Transcript storage location (optional)
TRANSCRIPT_DIR = os.getenv('TRANSCRIPT_DIR', os.path.expanduser('/path/to/save/transcripts'))