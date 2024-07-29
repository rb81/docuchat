import logging
import re

logger = logging.getLogger(__name__)

class CitationManager:
    @staticmethod
    def format_citations(response):
        logger.info("Formatting citations in response")
        logger.debug(f"Original response: {response}")
        
        # Regular expression to find citations with the special character
        citation_pattern = r'\[(¶[^\]]+)\]'
        
        # Find all citations in the response
        citations = re.findall(citation_pattern, response)
        
        if not citations:
            logger.warning("No citations found in the response")
            return response
        
        # Create a dictionary of unique citations
        unique_citations = {}
        citation_map = {}
        reference_count = 1
        
        for citation in citations:
            if citation not in citation_map:
                citation_map[citation] = reference_count
                unique_citations[reference_count] = citation.replace('¶', '').strip()
                reference_count += 1
        
        # Replace original citations with numbered references
        formatted_response = response
        for citation in citations:
            citation_number = citation_map[citation]
            original_citation = f"[{citation}]"
            formatted_response = formatted_response.replace(original_citation, f"[{citation_number}]")
        
        # Add the full citations at the end of the response
        formatted_response = formatted_response.rstrip()  # Remove trailing whitespace
        formatted_response += "\n\nReferences:"
        for i in sorted(unique_citations.keys()):
            formatted_response += f"\n\n{i}. {unique_citations[i]}"
        
        logger.debug(f"Formatted response: {formatted_response}")
        return formatted_response