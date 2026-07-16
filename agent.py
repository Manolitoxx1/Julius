import google.generativeai as genai
from config import GEMINI_API_KEY
import json

# Configurar el API Key
genai.configure(api_key=GEMINI_API_KEY)

# Definimos la herramienta (Tool) que el agente puede llamar
def guardar_gasto(fecha: str, boleta: str, lugar: str, precio: int, detalle: str):
    """
    Guarda un gasto en la planilla. Llama a esta función SOLAMENTE cuando tengas los 5 datos requeridos.
    
    Args:
        fecha: La fecha de la compra en formato YYYY-MM-DD. (Debes calcularla si el usuario dice "ayer" o "hoy").
        boleta: El número de boleta, factura o comprobante.
        lugar: El lugar, comercio o tienda donde se realizó la compra.
        precio: El monto total de la compra (número entero).
        detalle: Una breve descripción de lo que se compró.
    """
    # Esta función en realidad no guardará en Sheets directamente (lo hará la UI tras confirmar),
    # sino que devolverá los datos estructurados en formato JSON al chat de Streamlit.
    return json.dumps({
        "status": "ready_to_save",
        "data": {
            "Fecha": fecha,
            "Boleta": boleta,
            "Lugar": lugar,
            "Precio": precio,
            "Detalle": detalle
        }
    })

def get_chat_session(history=None):
    """
    Inicializa una sesión de chat con el modelo de Gemini.
    """
    if history is None:
        history = []
        
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        tools=[guardar_gasto],
        system_instruction=(
            "Eres un asistente virtual encargado de registrar gastos de la empresa. "
            "Tu objetivo es extraer 5 datos obligatorios de los mensajes del usuario: "
            "Fecha, Boleta (o número de recibo), Lugar de compra, Precio, y Detalle. "
            "Si el usuario omite algún dato, debes preguntarle amable y directamente por el dato faltante. "
            "NO intentes adivinar datos, debes estar seguro. "
            "Cuando tengas los 5 datos confirmados, DEBES llamar a la función 'guardar_gasto' "
            "para procesar el registro."
        )
    )
    
    # Creamos un chat pasándole el historial de la sesión (si existe)
    chat = model.start_chat(history=history, enable_automatic_function_calling=False)
    return chat
