from dotenv import load_dotenv
import os
from dotenv import find_dotenv

from pathlib import Path
load_dotenv(find_dotenv())


class Settings:

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    LLAMA_API_KEY: str = os.getenv("LLAMA_EXTRACT_KEY")
settings = Settings()

class Paths:
    BASE_DIR = Path(__file__).resolve().parent.parent

    #SRC_DIR = BASE_DIR / "src"
    TOOLS_DIR = BASE_DIR / "tools"

    #llama
    LLAMA_DIR = BASE_DIR / "Llama"
    PROMPT_DIR = LLAMA_DIR / "prompts"
    SYSTEM_PROMPT_DIR = PROMPT_DIR / "system_prompt.md"
    EXTRACTION_SCHEMA_DIR = PROMPT_DIR / "extraction_schema.json"
    
    #data
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    BOOK_DIR = RAW_DIR / "jane-austen-pride-prejudice.txt"
    TEST_DIR = RAW_DIR / "test.txt"
    PROCESSED_DIR = DATA_DIR / "processed" 
    PRE_PROCESSED_DIR = DATA_DIR / "pre_processed"
paths = Paths()