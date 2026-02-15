import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ai_ssh.db")
CREDENTIALS_ENCRYPT_KEY = os.getenv("CREDENTIALS_ENCRYPT_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set. Please configure it in .env.")

if not CREDENTIALS_ENCRYPT_KEY:
    raise RuntimeError("CREDENTIALS_ENCRYPT_KEY is not set. Please configure it in .env.")
