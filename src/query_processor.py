import logging

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, indexer):
        self.indexer = indexer

    def process_query(self, query, source_dir=None):
        logger.info(f"Processing query: {query}")
        logger.info(f"Source directory: {source_dir or 'All'}")
        
        try:
            relevant_chunks = self.indexer.search(query, source_dir)
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks")
            
            for i, chunk in enumerate(relevant_chunks):
                logger.debug(f"Chunk {i+1}:")
                logger.debug(f"Source: {chunk.metadata.get('source', 'Unknown')}")
                logger.debug(f"Page: {chunk.metadata.get('page', 'N/A')}")
                logger.debug(f"Source Directory: {chunk.metadata.get('source_dir', 'Unknown')}")
                logger.debug(f"Content: {chunk.page_content[:100]}...")  # Log first 100 characters
            
            return relevant_chunks
        
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            return []