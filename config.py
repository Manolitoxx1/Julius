import os
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env (para uso local)
load_dotenv()

def get_secret(key, default=""):
    # Intentar leer desde Streamlit Secrets primero (Nube)
    if key in st.secrets:
        return st.secrets[key]
    # Si no, leer de las variables de entorno (Local)
    return os.getenv(key, default)

# API Key de Gemini
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

# IDs de Google Sheets
GOOGLE_SHEET_CAJA_CHICA_ID = get_secret("GOOGLE_SHEET_CAJA_CHICA_ID", "")
GOOGLE_SHEET_CAJA_GRANDE_ID = get_secret("GOOGLE_SHEET_CAJA_GRANDE_ID", "")

# Archivo de base de datos SQLite
DATABASE_PATH = "expense_manager.db"

# Ruta al archivo credentials.json para Google Sheets (Service Account)
GOOGLE_CREDENTIALS_PATH = "credentials.json"
