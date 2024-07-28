import os
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def scan_files(folder_path, show_progress=False):
    logger.info(f"Scanning files in folder: {folder_path}")
    supported_extensions = ('.pdf', '.txt', '.docx')
    files = []
    skipped_files = []
    error_files = []

    total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
    logger.info(f"Total files found in directory (including unsupported): {total_files}")

    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            try:
                if filename.lower().endswith(supported_extensions):
                    files.append(full_path)
                    logger.debug(f"Added supported file: {full_path}")
                else:
                    skipped_files.append(full_path)
                    logger.debug(f"Skipped unsupported file: {full_path}")
            except Exception as e:
                error_files.append(full_path)
                logger.error(f"Error processing file {full_path}: {str(e)}")

    logger.info(f"Total supported files found: {len(files)}")
    logger.info(f"Total unsupported files skipped: {len(skipped_files)}")
    logger.info(f"Total files with errors: {len(error_files)}")

    if show_progress:
        print(f"Found {len(files)} supported files to process.")
        print(f"Skipped {len(skipped_files)} unsupported files.")
        print(f"Encountered errors with {len(error_files)} files.")

    return files

def display_file_count(folder_path):
    total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
    supported_files = len(scan_files(folder_path))
    print(f"Total files in directory: {total_files}")
    print(f"Supported files found: {supported_files}")
    print(f"Supported file types: PDF, TXT, DOCX")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_directory = sys.argv[1]
        print(f"Scanning directory: {test_directory}")
        display_file_count(test_directory)
        scan_files(test_directory, show_progress=True)
    else:
        print("Please provide a directory path as an argument.")