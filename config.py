import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# API Key de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# IDs de Google Sheets (se pueden configurar más adelante)
GOOGLE_SHEET_CAJA_CHICA_ID = os.getenv("GOOGLE_SHEET_CAJA_CHICA_ID", "")
GOOGLE_SHEET_CAJA_GRANDE_ID = os.getenv("GOOGLE_SHEET_CAJA_GRANDE_ID", "")

# Archivo de base de datos SQLite
DATABASE_PATH = "expense_manager.db"

# Ruta al archivo credentials.json para Google Sheets (Service Account)
GOOGLE_CREDENTIALS_PATH = "credentials.json"
