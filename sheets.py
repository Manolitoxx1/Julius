import gspread
from google.oauth2.service_account import Credentials
import os
from config import GOOGLE_CREDENTIALS_PATH
from datetime import datetime

# Definimos los alcances (scopes) necesarios para Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    # 1. Intentar leer desde Streamlit Secrets (Ideal para la Nube)
    import streamlit as st
    import json
    
    if "GOOGLE_CREDENTIALS_JSON" in st.secrets:
        google_json_string = st.secrets["GOOGLE_CREDENTIALS_JSON"]
        creds_dict = json.loads(google_json_string)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
        
    # 2. Si no está en secretos, intentar variable de entorno (Local/Legacy)
    google_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if google_json_string:
        creds_dict = json.loads(google_json_string)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
        
    # 2. Si no hay variable, intentar leer el archivo local (Ideal para probar en PC)
    if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"Falta el archivo {GOOGLE_CREDENTIALS_PATH} o la variable de entorno GOOGLE_CREDENTIALS_JSON.")
    
    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

def append_expense_to_sheet(sheet_id: str, expense_data: dict):
    """
    Inserta una nueva fila de gasto en la planilla y la ordena por fecha.
    expense_data debe contener: Fecha, Boleta, Lugar, Precio, Detalle
    """
    client = get_sheets_client()
    sheet = client.open_by_key(sheet_id).sheet1 # Asumimos la primera pestaña
    
    # Formateamos los datos para la fila
    # Asumimos que la hoja tiene las columnas en este orden: Fecha | Boleta | Lugar | Precio | Detalle
    row = [
        expense_data.get("Fecha", ""),
        expense_data.get("Boleta", ""),
        expense_data.get("Lugar", ""),
        expense_data.get("Precio", ""),
        expense_data.get("Detalle", "")
    ]
    
    # 1. Insertamos la nueva fila al final (append_row maneja buscar la próxima fila vacía)
    sheet.append_row(row)
    
    # 2. Ordenamos toda la hoja cronológicamente usando la columna Fecha (columna A = index 1 en API)
    # Obtenemos todos los datos para ver si tienen encabezado
    all_values = sheet.get_all_values()
    if len(all_values) > 1:
        # Ordenamos los datos excluyendo la primera fila de encabezados
        # gspread sort() function: sort((column_index, order ('asc' o 'des')))
        # Nota: gspread's sort method sorts strings. Si la fecha es DD/MM/YYYY, un sort de string no funcionará bien.
        # Es mejor requerir que el formato en gsheets sea numérico, o reformatearlo a YYYY-MM-DD temporalmente.
        # Para que funcione correctamente en Sheets, 'Fecha' debe ser AAAA-MM-DD o Google Sheets debe detectar
        # automáticamente la celda como fecha para usar un ordenamiento nativo en la UI.
        # Aquí usaremos el sort nativo de gspread asumiendo que Sheets las reconoce como fechas,
        # o alternativamente el Agente extraerá la fecha en YYYY-MM-DD.
        
        # Ojo: la API de Sheets requiere el formato de índice '1' para la columna A.
        # Pero gspread sort() funciona en el rango completo.
        # La forma más segura es usar sort nativo de rango omitiendo el encabezado:
        
        # sheet.sort((1, 'asc'), range='A2:E') # Rango sin encabezado (Requiere versión gspread que lo soporte, lo más fácil es usar update)
        
        # Un enfoque más seguro usando gspread >= 6.0:
        # Obtener el número total de filas
        total_rows = len(all_values)
        if total_rows > 1:
            sheet.sort((1, 'asc'), range=f'A2:E{total_rows}')

    return True
