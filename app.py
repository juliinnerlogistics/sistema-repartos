import streamlit as st
import os, base64, requests, urllib.parse, pandas as pd
from shapely.geometry import Point, Polygon
from pykml import parser

# --- CONFIGURACIÓN Y CARPETAS ---
st.set_page_config(page_title="INNER LOGISTICS", layout="wide")
FOLDER_ZONAS = "zonas"
if not os.path.exists(FOLDER_ZONAS): 
    os.makedirs(FOLDER_ZONAS)

# --- BASE DE DATOS DE CHOFERES ---
DB = {
    "MENEGHIN GABRIEL LUIS": "5493413040368", "JUAN JOSE, CISNEROS": "5493412501746",
    "PARDO JUAN IGNACIO": "5493416589548", "JOSE, CAPPUCCIO": "5493416728180",
    "ROMERO SERGIO": "5493425517414", "MARCOS MARTINEZ": "5493416181394",
    "VRANCICH DIEGO": "5493416563798", "MAXIMILIANO SEBES": "5493415601516",
    "CLAUDIO ROMERO": "5493413083314", "JESúS AGUILERA": "5493413768478",
    "MARCOS WENK": "5493425517414", "ALEJANDRA FERRARO": "5493413021451",
    "HUGO MARTINUCCI": "5493415870243", "FERNANDO GIANNI": "5493413099216",
    "FERNANDO MANSILLA": "5493416843864", "SEBASTIAN GARCIA": "5493412615425",
    "JONATAN SCHUMAKER": "5493425517414", "DAMIáN FLAMENCO": "5493414004879",
    "CRISTIAN SANGUINETTI": "5493412806479", "OMAR MIGUEL RAMIREZ": "5493416748237",
    "CANAVO, CRISTIAN MARTIN": "5493402523716", "EREZUMA MARTIN": "5493416194298",
    "ANGULO DIEGO": "5493415624965", "GANANOPULO NICOLAS": "5493416596751",
    "PERRETTA ROMINA": "5493416176424", "DATTO ACTIS ADRIAN": "5493364277548",
    "RODRIGUEZ PABLO MARIANO": "5493416136973", "PRADO WILBER": "5493417195251"
}

# --- ESTILOS VISUALES (CORREGIDOS CON DOBLE LLAVE) ---
def aplicar_estilo_v86(fnd):
    b64 = ""
    if os.path.exists(fnd):
        with open(fnd, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(255,255,255,0.7),rgba(255,255,255,0.7)), url("data:image/png;base64,{b64}"); 
        background-size: cover; background-attachment: fixed; 
    }}
    .res-card {{ background: #1E3A8A; border: 10px solid #FACC15; border-radius: 30px; padding: 60px; text-align: center; }}
    .txt-gigante {{ color: white; font-size: 80px; font-weight: bold; }}
    .kpi-box {{ background: #1E3A8A; color: white; padding: 20px; border-radius: 15px; text-align: center; border-bottom: 6px solid #FACC15; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE MAPAS ---
@st.cache_data(show_spinner=False)
def buscar_zona_optimizada(dire):
    if len(dire.strip()) < 3: return "⚠️ Dirección corta."
    u = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(dire+', Rosario, AR')}&format=json&limit=1"
    try:
        r = requests.get(u, headers={'User-Agent':'InnerV2'}, timeout=10).json()
        if not r: return "❌ No encontrada."
        p = Point(float(r[0]['lat']), float(r[0]['lon']))
        for fk in [f for f in os.listdir(FOLDER_ZONAS) if f.endswith('.kml')]:
            with open(os.path.join(FOLDER_ZONAS, fk), 'rb') as k:
                rt = parser.parse(k).getroot()
                for pm in rt.Document.iterfind('.//{{http://www.opengis.net/kml/2.2}}Placemark'):
                    if hasattr(pm, 'Polygon'):
                        co = pm.Polygon.outerBoundaryIs.LinearRing.coordinates.text.strip().split()
                        pts = [(float(i.split(',')[1]), float(i.split(',')[0])) for i in co]
                        if Polygon(pts).contains(p): return f"ZONA: {pm.name.text}"
        return "📍 Fuera de radio."
    except: return "⚙️ Error de conexión."

# --- ESTADOS DE SESIÓN ---
if "pg" not in st.session_state: st.session_state.pg = "buscar"
if "idx" not in st.session_state: st.session_state.idx = 0

# --- MENÚ LATERAL ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("INNER LOGISTICS")
    
    st.markdown("---")
    if st.button("🔎 Buscador", use_container_width=True): 
        st.session_state.pg = "buscar"; st.rerun()
    if st.button("📋 APP Remitos Suizo", use_container_width=True): 
        st.session_state.pg = "pendientes"; st.rerun()
    if st.button("📂 Cargar Mapas", use_container_width=True): 
        st.session_state.pg = "carga"; st.rerun()

# --- VISTA: BUSCADOR ---
if st.session_state.pg == "buscar":
    aplicar_estilo_v86("fondo_consultas.png")
    ent = st.text_input("Ingrese Dirección (Calle y Altura):")
    if st.button("VERIFICAR ZONA") and ent:
        res = buscar_zona_optimizada(ent)
        if "ZONA:" in res:
            st.markdown(f'<div class="res-card"><p class="txt-gigante">{res.replace("ZONA: ","")}</p></div>', unsafe_allow_html=True)
        else: st.error(res)

# --- VISTA: PENDIENTES (SUIZO) ---
elif st.session_state.pg == "pendientes":
    aplicar_estilo_v86("fondo_pendientes.png")
    st.title("APP Remitos Suizo")
    fl = st.file_uploader("Subir reporte Excel/CSV", type=["xlsx", "csv"])
    if fl:
        df = pd.read_csv(fl) if fl.name.endswith('.csv') else pd.read_excel(fl)
        pnd = df[(df['Nombre del Chofer'].isin(DB.keys())) & (df['Pendientes'] > 0)].copy()
        pnd['Pct_Carga'] = pnd.apply(lambda r: int(((r['Total'] - r['Pendientes']) / r['Total']) * 100) if r['Total'] > 0 else 0, axis=1)
        chs = sorted(pnd['Nombre del Chofer'].unique())
        
        if chs and st.session_state.idx < len(chs):
            c = chs[st.session_state.idx]
            d = pnd[pnd['Nombre del Chofer'] == c]
            txt_suizo = "¡Buenos días! Les paso el listado de hojas de ruta pendientes. Por favor, no olviden actualizar el sistema lo antes posible para evitar retrasos en el cierre del día."
            msg = f"*INNER LOGISTICS*\n\n{txt_suizo}\n\n*Chofer:* {c}\n"
            msg += "\n".join([f"• HR: {r['Hoja de Ruta']} - {r['Pendientes']} pnd. (Carga: {r['Pct_Carga']}%)" for _, r in d.iterrows()])
            
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="kpi-box"><h4>PENDIENTES</h4><h2>{int(pnd["Pendientes"].sum())}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="kpi-box"><h4>CHOFER</h4><h2>{st.session_state.idx + 1}/{len(chs)}</h2></div>', unsafe_allow_html=True)
            
            st.subheader(f"Enviando a: {c}")
            st.dataframe(d[['Hoja de Ruta', 'Total', 'Pendientes', 'Pct_Carga']], use_container_width=True)
            
            u_wa = f"https://wa.me/{DB[c]}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{u_wa}" target="_blank"><button style="width:100%;background:#25D366;color:white;padding:15px;border-radius:10px;border:none;cursor:pointer;font-weight:bold;font-size:18px;">📲 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
            
            if st.button("SIGUIENTE CHOFER ➡️", use_container_width=True): 
                st.session_state.idx += 1; st.rerun()
        else:
            st.success("✅ Gestión de remitos completada.")
            if st.button("🔄 REINICIAR"): 
                st.session_state.idx = 0; st.rerun()

# --- VISTA: CARGA KML ---
elif st.session_state.pg == "carga":
    aplicar_estilo_v86("fondo_masiva.png")
    ks = st.file_uploader("Seleccione archivos", accept_multiple_files=True)
    if st.button("GUARDAR EN CARPETA"):
        for k in ks:
            with open(os.path.join(FOLDER_ZONAS, k.name), "wb") as f: 
                f.write(k.getbuffer())
        st.success("Archivos guardados correctamente.")
        st.cache_data.clear()