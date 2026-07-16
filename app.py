import streamlit as st
import json
from agent import get_chat_session
from database import standardize_place
from sheets import append_expense_to_sheet
from config import GOOGLE_SHEET_CAJA_CHICA_ID, GOOGLE_SHEET_CAJA_GRANDE_ID

st.set_page_config(page_title="Gestor de Gastos AI", page_icon="💸", layout="centered")

# Inyectar CSS personalizado para hacer la letra más grande
st.markdown("""
    <style>
    /* Aumentar el tamaño base de toda la aplicación */
    html, body, [class*="css"]  {
        font-size: 20px !important;
    }
    /* Aumentar el tamaño de los inputs y botones */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stButton button {
        font-size: 18px !important;
    }
    /* Aumentar el tamaño de los mensajes del chat */
    .stChatMessage {
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- UI Sidebar: Selección de Caja ---
st.sidebar.title("Configuración")
caja_seleccionada = st.sidebar.selectbox(
    "Selecciona la Caja / Planilla",
    ("Caja Chica", "Caja Grande")
)

# Mapeamos la selección a su respectivo Sheet ID
sheet_ids = {
    "Caja Chica": GOOGLE_SHEET_CAJA_CHICA_ID,
    "Caja Grande": GOOGLE_SHEET_CAJA_GRANDE_ID
}
active_sheet_id = sheet_ids[caja_seleccionada]

# --- Manejo de Estado (Session State) ---
# Usamos un session_state separado para cada caja para mantener conversaciones independientes
state_key = f"chat_history_{caja_seleccionada}"
if state_key not in st.session_state:
    st.session_state[state_key] = []
    
# Estado para manejar si hay un gasto pendiente de confirmación
pending_key = f"pending_expense_{caja_seleccionada}"
if pending_key not in st.session_state:
    st.session_state[pending_key] = None

# Mostramos un mensaje de advertencia si no hay un ID configurado
if not active_sheet_id or active_sheet_id == "your_caja_chica_sheet_id_here":
    st.warning(f"⚠️ El ID de Google Sheets para {caja_seleccionada} no está configurado en .env")

st.title(f"💸 Registro de Gastos - {caja_seleccionada}")
st.write("Ingresa los detalles de tu compra. Ejemplo: *Ayer compré hojas para la impresora en el líder por 3500, boleta 90*")

# --- Renderizar historial de chat ---
for msg in st.session_state[state_key]:
    # Streamlit no sabe renderizar directamente los objetos de historial de genai
    # Así que guardamos un historial paralelo simplificado para la UI
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Lógica de Confirmación de Gasto ---
if st.session_state[pending_key]:
    expense = st.session_state[pending_key]
    st.info("📊 **Resumen del Gasto a Guardar**")
    st.write(f"- **Fecha:** {expense['Fecha']}")
    st.write(f"- **Boleta:** {expense['Boleta']}")
    st.write(f"- **Lugar:** {expense['Lugar']} *(Estandarizado)*")
    st.write(f"- **Precio:** ${expense['Precio']}")
    st.write(f"- **Detalle:** {expense['Detalle']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar y Guardar", use_container_width=True):
            try:
                # Escribir en Google Sheets
                append_expense_to_sheet(active_sheet_id, expense)
                st.success("¡Gasto guardado exitosamente en Google Sheets!")
                # Limpiar el estado pendiente y añadir mensaje de éxito al chat
                st.session_state[state_key].append({"role": "assistant", "content": "¡Gasto guardado exitosamente! ¿Tienes otro gasto que registrar?"})
                st.session_state[pending_key] = None
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}. ¿Configuraste credentials.json?")
    with col2:
        if st.button("❌ Cancelar", type="secondary", use_container_width=True):
            st.session_state[pending_key] = None
            st.session_state[state_key].append({"role": "assistant", "content": "Registro cancelado. ¿En qué más puedo ayudarte?"})
            st.rerun()

# --- Input del Usuario ---
# Ocultamos el input si hay un gasto pendiente de confirmación
if not st.session_state[pending_key]:
    user_input = st.chat_input("Escribe los detalles del gasto...")

    if user_input:
        # Añadir al historial de la UI
        st.session_state[state_key].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                # Reconstruir el historial en formato genai
                # Limitamos el historial a los últimos 4 mensajes para que el bot responda muchísimo más rápido
                # y no lea todo el pasado irrelevante en cada consulta.
                genai_history = []
                mensajes_recientes = st.session_state[state_key][:-1][-4:] # Últimos 4 excluyendo el actual
                for m in mensajes_recientes: 
                    role = "user" if m["role"] == "user" else "model"
                    genai_history.append({"role": role, "parts": [m["content"]]})
                
                # Obtener la sesión
                chat = get_chat_session(history=genai_history)
                
                # Enviar el mensaje
                response = chat.send_message(user_input)
                
                # Buscar de forma segura si hay un function_call en las partes de la respuesta
                fc = None
                try:
                    for part in response.candidates[0].content.parts:
                        if getattr(part, "function_call", None):
                            fc = part.function_call
                            break
                except Exception:
                    pass
                
                if fc and fc.name == "guardar_gasto":
                    # Extraemos los argumentos de la herramienta y capitalizamos las llaves (Fecha, Boleta, etc.)
                    args = {}
                    for key, val in fc.args.items():
                        args[key.capitalize()] = val
                    
                    # Estandarizar el lugar con la Base de Datos local
                    lugar_estandarizado = standardize_place(args.get("Lugar", ""))
                    args["Lugar"] = lugar_estandarizado
                    
                    # Guardamos en pendiente
                    st.session_state[pending_key] = args
                    
                    # Notificamos al usuario
                    msg = "He extraído todos los datos. Por favor revisa y confirma."
                    st.markdown(msg)
                    st.session_state[state_key].append({"role": "assistant", "content": msg})
                    
                    # Recargamos para mostrar los botones de confirmación
                    st.rerun()
                else:
                    # Respuesta de texto normal (pidiendo más info)
                    respuesta_texto = response.text if hasattr(response, 'text') else "No entendí, ¿puedes repetir?"
                    st.markdown(respuesta_texto)
                    st.session_state[state_key].append({"role": "assistant", "content": respuesta_texto})
