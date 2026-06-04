import logging
import json
import time
import os
from datetime import datetime

# Setup logger
log_path = "/workspace/production/logs/app.log"
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("avaniko")

def log_request(endpoint, file_type, filename, api_key):
    logger.info(f"REQUEST | {endpoint} | {file_type} | {filename} | key:{api_key[:12]}...")

def log_ocr(filename, engine, confidence, text_len):
    logger.info(f"OCR | {filename} | engine:{engine} | conf:{confidence} | chars:{text_len}")

def log_llm(mode, tokens, response_ms, success):
    status = "✅" if success else "❌"
    logger.info(f"LLM | {status} | mode:{mode} | tokens:{tokens} | {response_ms}ms")

def log_error(endpoint, error, filename=""):
    logger.error(f"ERROR | {endpoint} | {filename} | {str(error)}")

def log_file_parse(filename, file_type, text_len, is_scanned):
    logger.info(f"PARSE | {filename} | {file_type} | chars:{text_len} | scanned:{is_scanned}")
