import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/tickets.db")