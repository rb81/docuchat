# DocuChat

![DocuChat](/header.png)

DocuChat is a simple Terminal RAG (Retrieval-Augmented Generation) application that allows you to talk to your files in complete privacy. Using Ollama, both the embedding and inference happens locally.

## Features

- **Document Processing**: Automatically processes PDF, TXT, and DOCX files from a specified directory.
- **Intelligent Indexing**: Creates and maintains an efficient index of document content for quick retrieval.
- **Natural Language Queries**: Allows users to ask questions in natural language about the content of their documents.
- **Citation Support**: Provides citations for information sources, linking responses directly to document pages.
- **Conversation Tracking**: Saves transcripts of conversations for future reference.
- **User-Friendly Interface**: Offers a clean, color-coded command-line interface for easy interaction.

## Prerequisites

- Python 3.8+
- Ollama (for running the LLM locally)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/rb81/docuchat.git
   cd docuchat
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application by editing the `config.py` file:
   ```python
   OLLAMA_BASE_URL = 'http://localhost:11434'
   OLLAMA_MODEL = 'llama3.1:latest'
   OLLAMA_EMBED_MODEL = 'nomic-embed-text'
   DOCUMENT_SOURCE_DIR = '/path/to/your/documents'
   DB_STORAGE_DIR = '/path/to/store/database'
   TRANSCRIPT_DIR = '/path/to/save/transcripts'
   ```

## Usage

1. Ensure Ollama is running with your chosen model.
2. Run the DocuChat application:
   ```
   python main.py
   ```

3. Start chatting! Ask questions about your documents, and DocuChat will provide answers with relevant citations.

4. Type `/quit` to exit the application and save your conversation transcript.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Transparency Disclaimer

[ai.collaboratedwith.me](ai.collaboratedwith.me) in creating this project.