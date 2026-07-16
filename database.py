import sqlite3
from config import DATABASE_PATH

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Tabla para mapear aliases de lugares al nombre oficial (estandarizado)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alias TEXT UNIQUE NOT NULL,
            official_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def standardize_place(place_name: str) -> str:
    """
    Busca si el 'place_name' ya tiene un nombre oficial en la base de datos.
    Si existe (buscando el alias en minúsculas), devuelve el nombre oficial.
    Si no existe, lo inserta con la primera letra en mayúscula como oficial y lo devuelve.
    """
    if not place_name:
        return place_name
    
    alias_lower = place_name.strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT official_name FROM places WHERE alias = ?", (alias_lower,))
    row = cursor.fetchone()
    
    if row:
        official_name = row["official_name"]
        conn.close()
        return official_name
    else:
        # Si no existe, creamos el nombre oficial (Capitalizado)
        official_name = place_name.strip().title()
        cursor.execute("INSERT INTO places (alias, official_name) VALUES (?, ?)", (alias_lower, official_name))
        conn.commit()
        conn.close()
        return official_name

# Inicializar la base de datos al importar el módulo
init_db()
