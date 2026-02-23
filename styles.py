# VERSION: INNER_CORE_V6 - UI FIX
import streamlit as st
import base64
import os

def aplicar_estilos_v6():
    fnd = "fondo_consultas.png"

    # Solo inyecta el fondo si el archivo existe, evitando URL rota en el CSS
    if os.path.exists(fnd):
        with open(fnd, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # FIX: era rgba(255,255,255,0.7) → blanco que tapaba la imagen.
        # Cambiado a negro semitransparente para que el texto blanco sea legible.
        fondo_css = f"""
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                        url("data:image/png;base64,{b64}");
            background-size: cover;
            background-attachment: fixed;
        }}
        """
    else:
        fondo_css = """
        .stApp {
            background: #0f1117;
        }
        """

    st.markdown(f"""
    <style>
    {fondo_css}

    /* Resultado GIGANTE 85px */
    .res-card {{
        background-color: #1E3A8A;
        border: 10px solid #FACC15;
        border-radius: 30px;
        padding: 60px;
        text-align: center;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
        margin-top: 20px;
    }}

    .txt-85 {{
        color: white;
        font-size: 85px;
        font-weight: 900;
        text-transform: uppercase;
        margin: 0;
    }}

    /* Botones Estilo Glossy Inner */
    .stButton > button {{
        border-radius: 12px;
        font-weight: 900;
        height: 60px;
        border: 2px solid #1E3A8A;
        transition: 0.3s;
    }}

    .stButton > button:hover {{
        background-color: #FACC15;
        color: #1E3A8A;
    }}
    </style>
    """, unsafe_allow_html=True)
