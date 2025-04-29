from dotenv import load_dotenv
import os

def load_config():
    load_dotenv()
    config = {}
    config['host'] = os.getenv("DB_HOST")
    config['user'] = os.getenv("DB_USER")
    config['password'] = os.getenv("DB_PASSWORD")
    config['database'] = os.getenv("DB_NAME")
    return config