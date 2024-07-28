import ollama
import logging
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

class LLMInterface:
    def __init__(self):
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model = OLLAMA_MODEL

    def generate_response(self, query, context_chunks):
        logger.info(f"Generating response for query: {query}")
        logger.info(f"Number of context chunks: {len(context_chunks)}")
        
        # Format the context chunks
        formatted_context = self._format_context(context_chunks)
        
        system_message = """You are a helpful assistant with access to specific document excerpts. When answering questions be sure to always follow these rules:

        1. Use information from the provided context to answer the user's questions.
        2. Cite your sources ALWAYS using the following format: [¶ Full_File_Path, Page: X]. For example: [¶ /path/to/document.pdf, Page: 10]
        3. If you need to combine information from multiple sources, cite each source separately. For example: [¶ /path/to/document1.pdf, Page: 10][¶ /path/to/document2.pdf, Page: 20]
        4. DO NOT refer to the excerpts directly, but use the content as the basis for your answers.
        5. If you're unsure or the context doesn't contain relevant information, say so.
        6. Do not invent or assume information not present in the given context."""

        user_message = f"Context:\n{formatted_context}\n\nQuestion: {query}"

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]

        logger.debug("Full input to LLM:")
        logger.debug(f"System message: {system_message}")
        logger.debug(f"User message: {user_message}")

        logger.info("Sending request to LLM")
        response = self.client.chat(model=self.model, messages=messages)
        logger.info("Received response from LLM")
        logger.debug(f"LLM raw response: {response}")
        
        return response['message']['content']

    def _format_context(self, context_chunks):
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks):
            source = chunk.metadata.get('source', 'Unknown')
            page = chunk.metadata.get('page', 'N/A')
            content = chunk.page_content
            formatted_chunks.append(f"Excerpt {i+1} from {source} (Page {page}):\n{content}\n")
        return "\n".join(formatted_chunks)