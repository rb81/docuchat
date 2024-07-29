import os

# Ollama settings
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:latest')
OLLAMA_EMBED_MODEL = os.getenv('OLLAMA_EMBED_MODEL', 'mxbai-embed-large')

# Document source directories
DOCUMENT_SOURCE_DIRS = os.getenv('DOCUMENT_SOURCE_DIR', [
    os.path.expanduser('/path/to/your/documents'), # A source
    #os.path.expanduser('/path/to/your/documents'), # And another source
    #os.path.expanduser('/path/to/your/documents') # And another source...
])

# Database storage location
DB_STORAGE_DIR = os.getenv('DB_STORAGE_DIR', os.path.expanduser('/path/to/store/database'))

# Transcript storage location (optional)
TRANSCRIPT_DIR = os.getenv('TRANSCRIPT_DIR', os.path.expanduser('/path/to/save/transcripts'))