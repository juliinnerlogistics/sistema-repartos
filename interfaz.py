# INNER_CORE_v6.8 - Interfaz Adaptativa
import streamlit as st
import base64
import os

def aplicar_diseno_premium(archivo_fondo):
    # Solo inyecta el fondo si el archivo existe, evitando URL rota en el CSS
    if os.path.exists(archivo_fondo):
        with open(archivo_fondo, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        fondo_css = f"""
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                        url("data:image/png;base64,{b64}");
            background-size: cover;
            background-attachment: fixed;
        }}
        """
    else:
        # Fondo sólido de respaldo si no existe la imagen
        fondo_css = """
        .stApp {
            background: #0f1117;
        }
        """

    st.markdown(f"""
    <style>
    {fondo_css}

    /* Cartas de Apps */
    .app-card {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }}

    .res-card {{
        background: #1E3A8A;
        border: 8px solid #FACC15;
        border-radius: 30px;
        padding: 40px;
        text-align: center;
    }}

    .txt-85 {{
        color: white;
        font-size: 85px;
        font-weight: 900;
        margin: 0;
    }}

    /* Botones Universales */
    div.stButton > button {{
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        background: linear-gradient(145deg, #1e3a8a, #1e40af) !important;
        color: white !important;
        border: 1px solid #FACC15 !important;
    }}

    [data-testid="stSidebar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)
