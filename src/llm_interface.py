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
        
        user_message = f"""You are a helpful assistant with access to specific document excerpts. When answering questions, always follow these rules:

        1. Use information from the provided context to answer the user's questions.
        2. Cite your sources ALWAYS using the following format: [¶ Full_File_Path, Page: X]. For example: [¶ /path/to/document.pdf, Page: 10]
        3. If you need to combine information from multiple sources, cite each source separately. For example: [¶ /path/to/document1.pdf, Page: 10][¶ /path/to/document2.pdf, Page: 20]
        4. DO NOT refer to the excerpts directly, but use the content as the basis for your answers.
        5. If you're unsure or the context doesn't contain relevant information, say so.
        6. Do not invent or assume information not present in the given context.

        Example:
        Context:
        Excerpt 1 from /path/to/document1.pdf (Page 10):
        The sky is blue.

        Excerpt 2 from /path/to/document2.pdf (Page 20):
        Grass is green.

        Question: What color is the sky and the grass?
        Answer: The sky is blue [¶ /path/to/document1.pdf, Page: 10] and the grass is green [¶ /path/to/document2.pdf, Page: 20].
        
        Context:
        
        {formatted_context}
        
        Question:
        
        {query}"""

        messages = [
            {'role': 'user', 'content': user_message}
        ]

        logger.debug("Full input to LLM:")
        logger.debug(f"User message: {user_message}")

        logger.info("Sending request to LLM")
        response = self.client.chat(model=self.model, messages=messages)
        logger.info("Received response from LLM")
        logger.debug(f"LLM raw response: {response}")
        
        # Post-process the response to ensure it follows the rules
        processed_response = self._post_process_response(response['message']['content'], context_chunks)
        
        return processed_response

    def _format_context(self, context_chunks):
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks):
            source = chunk.metadata.get('source', 'Unknown')
            page = chunk.metadata.get('page', 'N/A')
            content = chunk.page_content
            formatted_chunks.append(f"Excerpt {i+1} from {source} (Page {page}):\n{content}\n")
        return "\n".join(formatted_chunks)

    def _post_process_response(self, response, context_chunks):
        # Check if the response follows the citation format
        for chunk in context_chunks:
            source = chunk.metadata.get('source', 'Unknown')
            page = chunk.metadata.get('page', 'N/A')
            citation = f"[¶ {source}, Page: {page}]"
            if citation not in response:
                logger.warning(f"Response missing citation for source {source} page {page}")
                # You can add additional logic here to handle missing citations
        return response