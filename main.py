import os, sys
import textwrap
import logging
from datetime import datetime
from colorama import init, Fore, Style
import time
import signal
import threading
from src.file_handler import scan_files, display_file_count
from src.document_processor import process_documents
from src.indexer import Indexer
from src.query_processor import QueryProcessor
from src.llm_interface import LLMInterface
from src.citation_manager import CitationManager
from config import DOCUMENT_SOURCE_DIR, DB_STORAGE_DIR, TRANSCRIPT_DIR

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

init(autoreset=True)  # Initialize colorama

class DocuChat:
    def __init__(self):
        self.indexer = None
        self.query_processor = None
        self.llm_interface = None
        self.response_cache = {}
        self.conversation = []
        self.thinking = False
        self.thinking_thread = None
        signal.signal(signal.SIGINT, self.signal_handler)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def setup_rag_system(self):
        logger.info(f"Setting up DocuChat. Using source directory: {DOCUMENT_SOURCE_DIR}")
        logger.info(f"Database storage directory: {DB_STORAGE_DIR}")
        
        if os.path.isdir(DOCUMENT_SOURCE_DIR):
            print(f"{Fore.CYAN}Analyzing directory contents...{Style.RESET_ALL}\n")
            display_file_count(DOCUMENT_SOURCE_DIR)
            
            print(f"\n{Fore.CYAN}Scanning and processing files...{Style.RESET_ALL}\n")
            files = scan_files(DOCUMENT_SOURCE_DIR, show_progress=True)
            logger.info(f"Found {len(files)} supported files to process")
            
            self.indexer = Indexer()
            
            if self.indexer.check_for_changes(files):
                logger.info("Changes detected in documents. Reprocessing...")
                chunks = process_documents(files, show_progress=True)
                logger.info(f"Processed documents into {len(chunks)} chunks")
                
                print(f"{Fore.CYAN}Creating index...{Style.RESET_ALL}")
                self.indexer.create_index(chunks, show_progress=True)
                self.indexer.cache_document_hashes(files)
                logger.info(f"Index created and stored in {self.indexer.persist_directory}")
            else:
                logger.info("No changes detected in documents. Using existing index.")
            
            self.query_processor = QueryProcessor(self.indexer)
            self.llm_interface = LLMInterface()
            logger.info(f"DocuChat setup complete. Processed {len(files)} files.")
            print(f"\n{Fore.GREEN}Setup complete. Processed {len(files)} files.{Style.RESET_ALL}\n")
        else:
            logger.error(f"Invalid source directory: {DOCUMENT_SOURCE_DIR}")
            raise ValueError(f"Invalid source directory: {DOCUMENT_SOURCE_DIR}. Please check your configuration.")

    def print_user_query(self, query):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}[{timestamp}] User:{Style.RESET_ALL}\n")
        print(f"{Fore.WHITE}{textwrap.fill(query, width=80)}\n")
        self.conversation.append(f"**User**: {query}\n")

    def print_assistant_response(self, response):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{Fore.GREEN}{Style.BRIGHT}[{timestamp}] Assistant:{Style.RESET_ALL}\n")
        
        paragraphs = response.split('\n\n')
        for paragraph in paragraphs:
            print(f"{Fore.CYAN}{textwrap.fill(paragraph, width=80)}\n")
        
        self.conversation.append(f"**Assistant**: {response}\n")

    def thinking_animation(self):
        animation = "|/-\\"
        idx = 0
        while self.thinking:
            sys.stdout.write(f"\r{Style.BRIGHT}Assistant is thinking... {animation[idx % len(animation)]}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
        sys.stdout.write('\033[K\033[1A\033[K')
        sys.stdout.flush()

    def start_thinking_animation(self):
        self.thinking = True
        self.thinking_thread = threading.Thread(target=self.thinking_animation)
        self.thinking_thread.start()

    def stop_thinking_animation(self):
        if self.thinking:
            self.thinking = False
            if self.thinking_thread:
                self.thinking_thread.join()

    def signal_handler(self, sig, frame):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Interrupt received. Saving transcript and exiting...")
        self.stop_thinking_animation()
        self.save_transcript()
        sys.exit(0)

    def save_transcript(self):
        if TRANSCRIPT_DIR and len(self.conversation) >= 2:  # Check if there's at least one user message and one assistant message
            os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{timestamp}.md"
            filepath = os.path.join(TRANSCRIPT_DIR, filename)
            
            with open(filepath, 'w') as f:
                f.write("# DocuChat Transcript\n\n")
                for entry in self.conversation:
                    f.write(entry + "\n")
            
            print(f"{Fore.MAGENTA}Transcript saved to: {filepath}")
        else:
            print(f"{Fore.YELLOW}No transcript saved. Either no conversation or no transcript directory specified.")


    def get_user_input(self):
        sys.stdout.write(f"{Fore.YELLOW}{Style.BRIGHT}You:{Style.RESET_ALL} ")
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()
        sys.stdout.write('\033[1A\033[K\033[1A')  # Move up and clear the entire line
        sys.stdout.flush()
        return user_input

    def run(self):
        self.clear_screen()
        self.setup_rag_system()

        if not self.query_processor or not self.llm_interface:
            logger.error("DocuChat setup failed.")
            print(f"{Fore.RED}{Style.BRIGHT}DocuChat setup failed. Please restart the application.")
            return

        input(f"{Fore.YELLOW}{Style.BRIGHT}Press Enter to begin...{Style.RESET_ALL}")
        self.clear_screen()

        print(f"{Fore.MAGENTA}{Style.BRIGHT}Welcome to DocuChat!")
        print(f"{Fore.MAGENTA}Type your queries or use /quit to exit.\n")

        while True:
            user_input = self.get_user_input()

            if user_input.lower() == '/quit':
                print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Saving transcript and exiting...")
                self.save_transcript()
                print(f"{Fore.MAGENTA}{Style.BRIGHT}Goodbye!")
                break

            self.print_user_query(user_input)

            try:
                self.start_thinking_animation()
                context_chunks = self.query_processor.process_query(user_input)
                logger.info(f"Retrieved {len(context_chunks)} relevant chunks")
                
                response = self.llm_interface.generate_response(user_input, context_chunks)
                logger.info("Generated response from LLM")
                logger.debug(f"Raw LLM response: {response}")
                
                formatted_response = CitationManager.format_citations(response)
                logger.info("Formatted citations in response")
                logger.debug(f"Formatted response: {formatted_response}")
                
                if user_input in self.response_cache:
                    logger.warning("Inconsistent responses detected for the same query:")
                    logger.warning(f"Previous response: {self.response_cache[user_input]}")
                    logger.warning(f"Current response: {formatted_response}")
                
                self.response_cache[user_input] = formatted_response
                
                self.stop_thinking_animation()
                self.print_assistant_response(formatted_response)
                
            except Exception as e:
                self.stop_thinking_animation()
                logger.error(f"An error occurred: {str(e)}", exc_info=True)
                print(f"{Fore.RED}\nAn error occurred: {str(e)}")

        # Ensure thinking animation is stopped when exiting the loop
        self.stop_thinking_animation()

if __name__ == "__main__":
    app = DocuChat()
    app.run()