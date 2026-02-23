import streamlit as st
from interfaz import aplicar_diseno_premium
from datos import consultar_zona, CHOFERES

st.set_page_config(page_title="INNER LOGISTICS Panel de Control", layout="wide")
aplicar_diseno_premium("fondo_consultas.png")

if "menu" not in st.session_state:
    st.session_state.menu = "TRAFICO"

st.markdown(
    "<h1 style='text-align:center; color:white;'>INNER LOGISTICS Panel de Control</h1>",
    unsafe_allow_html=True
)
st.write("---")

c1, c2 = st.columns(2)
with c1:
    if st.button("🚛 TRÁFICO", use_container_width=True):
        st.session_state.menu = "TRAFICO"
        st.rerun()
with c2:
    if st.button("📱 APPS", use_container_width=True):
        st.session_state.menu = "APPS"
        st.rerun()

if st.session_state.menu == "TRAFICO":
    st.subheader("Buscador de Repartos")
    dir_in = st.text_input("Ingrese Calle y Altura (Rosario):")

    if st.button("IDENTIFICAR REPARTO") and dir_in:
        with st.spinner("Procesando..."):
            res = consultar_zona(dir_in)
        if "❌" in res or "🔍" in res or "⚠️" in res:
            st.error(res)
        else:
            st.success(res)

elif st.session_state.menu == "APPS":
    import base64, os

    def logo_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return ""

    def app_card(logo_path, url, label):
        b64 = logo_b64(logo_path)
        img_html = (
            f'<img src="data:image/png;base64,{b64}" style="max-height:80px; max-width:100%; object-fit:contain; margin-bottom:12px;">' 
            if b64 else f'<div style="color:#aaa;font-size:0.9rem;margin-bottom:12px;">{label}</div>'
        )
        if url:
            st.markdown(f'''
                <a href="{url}" target="_blank" style="text-decoration:none;">
                    <div style="
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.15);
                        border-radius: 16px;
                        padding: 24px 16px;
                        text-align: center;
                        cursor: pointer;
                        transition: 0.2s;
                        backdrop-filter: blur(10px);
                    ">
                        {img_html}
                    </div>
                </a>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div style="
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.15);
                    border-radius: 16px;
                    padding: 24px 16px;
                    text-align: center;
                    backdrop-filter: blur(10px);
                ">
                    {img_html}
                    <div style="color:#aaa; font-size:0.75rem;">(Sin enlace configurado)</div>
                </div>
            ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        app_card("logo_suizo.png", None, "LOG-IN SUIZO")
        # --- Carga de Excel y generación de WhatsApp ---
        archivo = st.file_uploader("📂 Cargar reporte HR pendientes", type=["xlsx"], key="hr_upload")
        if archivo:
            import pandas as pd, re, urllib.parse, unicodedata, json
            from datetime import date, datetime

            def normalizar_nombre(s):
                """Normaliza nombre: mayúsculas, sin tildes, solo letras, palabras > 2 chars."""
                s = s.upper().strip()
                s = unicodedata.normalize("NFD", s)
                s = "".join(c for c in s if unicodedata.category(c) != "Mn")
                s = re.sub(r"[^A-Z ]", " ", s)
                return set(w for w in s.split() if len(w) > 2)

            # Precalcular palabras de cada clave del diccionario CHOFERES
            choferes_norm = {k: normalizar_nombre(k) for k in CHOFERES}

            def buscar_chofer(nombre_excel):
                """Busca el chofer por coincidencia de palabras (tolera orden y tildes)."""
                palabras = normalizar_nombre(nombre_excel)
                mejor_clave, mejor_score = None, 0
                for clave, palabras_clave in choferes_norm.items():
                    score = len(palabras & palabras_clave)
                    if score > mejor_score:
                        mejor_score = score
                        mejor_clave = clave
                return (mejor_clave, CHOFERES[mejor_clave]) if mejor_score >= 2 else None

            df = pd.read_excel(archivo, header=0)
            df.columns = [
                "Hoja_Ruta","Estado","Fecha_HR","Reparto","SubReparto","Nombre_Reparto",
                "Fecha_Reparto","Cod_Chofer","Nombre_Chofer","Celular",
                "Total","Pendientes","Entregadas","Rechazadas","Reprogramadas","Retiro","Anulada"
            ]
            df["Pendientes"] = pd.to_numeric(df["Pendientes"], errors="coerce").fillna(0).astype(int)
            df_pend = df[df["Pendientes"] > 0].copy()

            # --- KPIs globales ---
            df["Total"]      = pd.to_numeric(df["Total"],      errors="coerce").fillna(0).astype(int)
            df["Entregadas"] = pd.to_numeric(df["Entregadas"], errors="coerce").fillna(0).astype(int)

            total_hdr      = len(df)
            total_total    = df["Total"].sum()
            total_entregadas = df["Entregadas"].sum()
            pct_entregado  = round(total_entregadas / total_total * 100, 1) if total_total > 0 else 0
            choferes_pend  = df_pend["Nombre_Chofer"].nunique() if not df_pend.empty else 0
            hdr_pendientes = len(df_pend)

            # Fecha extraída del nombre del archivo Excel (ej: resumenHR20260220040150.xlsx → 2026-02-20)
            import re as _re
            _m = _re.search(r"(\d{4})(\d{2})(\d{2})", archivo.name)
            if _m:
                fecha_archivo = f"{_m.group(1)}-{_m.group(2)}-{_m.group(3)}"
            else:
                fecha_archivo = date.today().isoformat()
            fecha_display = datetime.strptime(fecha_archivo, "%Y-%m-%d").strftime("%d/%m/%Y")

            # --- Tarjetas KPI grandes (horizontal) ---
            color_pct = "#4ADE80" if pct_entregado >= 90 else "#F87171"
            st.markdown(f"<h3 style='color:white; text-align:center;'>📊 KPIs al {fecha_display}</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style='display:flex; gap:16px; margin:12px 0;'>
                    <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                border-radius:16px; padding:20px 12px; text-align:center;'>
                        <div style='font-size:54px; font-weight:900; color:white; line-height:1'>{choferes_pend}</div>
                        <div style='color:#ccc; font-size:0.82rem; margin-top:6px;'>Choferes con pendientes</div>
                    </div>
                    <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                border-radius:16px; padding:20px 12px; text-align:center;'>
                        <div style='font-size:54px; font-weight:900; color:white; line-height:1'>{hdr_pendientes}</div>
                        <div style='color:#ccc; font-size:0.82rem; margin-top:6px;'>HRs pendientes</div>
                    </div>
                    <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                border-radius:16px; padding:20px 12px; text-align:center;'>
                        <div style='font-size:54px; font-weight:900; color:{color_pct}; line-height:1'>{pct_entregado}%</div>
                        <div style='color:#ccc; font-size:0.82rem; margin-top:6px;'>Entregado sobre total</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # --- Gráfico de barras por chofer ---
            import plotly.graph_objects as go

            df_chart = df.groupby("Nombre_Chofer").agg(
                Entregadas=("Entregadas", "sum"),
                Pendientes=("Pendientes", "sum"),
                Total=("Total", "sum")
            ).reset_index()
            df_chart = df_chart[df_chart["Total"] > 0].copy()
            df_chart["Pct"] = (df_chart["Entregadas"] / df_chart["Total"] * 100).round(1)
            df_chart = df_chart.sort_values("Pendientes", ascending=False)

            # Abreviar nombres largos para el eje X
            df_chart["NombreCorto"] = df_chart["Nombre_Chofer"].apply(
                lambda n: " ".join(n.split()[:2])
            )

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Entregadas",
                x=df_chart["NombreCorto"],
                y=df_chart["Entregadas"],
                marker_color="#4ADE80",
                text=df_chart["Entregadas"],
                textposition="inside",
                textfont=dict(color="white", size=11)
            ))
            fig.add_trace(go.Bar(
                name="Pendientes",
                x=df_chart["NombreCorto"],
                y=df_chart["Pendientes"],
                marker_color="#F87171",
                text=df_chart["Pendientes"],
                textposition="inside",
                textfont=dict(color="white", size=11)
            ))
            # Línea de % entregado sobre eje secundario
            fig.add_trace(go.Scatter(
                name="% Entregado",
                x=df_chart["NombreCorto"],
                y=df_chart["Pct"],
                mode="lines+markers+text",
                text=[f"{p}%" for p in df_chart["Pct"]],
                textposition="top center",
                textfont=dict(
                    color=[("#4ADE80" if p >= 90 else "#F87171") for p in df_chart["Pct"]],
                    size=10, family="Arial Black"
                ),
                marker=dict(size=8, color=[("#4ADE80" if p >= 90 else "#F87171") for p in df_chart["Pct"]]),
                line=dict(color="white", width=1.5, dash="dot"),
                yaxis="y2"
            ))
            fig.update_layout(
                barmode="stack",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(color="white")),
                xaxis=dict(tickfont=dict(size=10, color="white"), gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="Cantidad", gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color="white")),
                yaxis2=dict(title="% Entregado", overlaying="y", side="right",
                            range=[0, 115], ticksuffix="%", tickfont=dict(color="white"),
                            showgrid=False),
                margin=dict(t=30, b=10, l=10, r=10),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Guardar en histórico automáticamente ---
            HIST_FILE = "kpi_historico.json"
            historico = {}
            if os.path.exists(HIST_FILE):
                with open(HIST_FILE, "r", encoding="utf-8") as f:
                    historico = json.load(f)

            # Detalle por chofer para el histórico
            grupos_all = df.groupby("Nombre_Chofer")
            detalle_choferes = {}
            for nombre, grupo in grupos_all:
                match = buscar_chofer(nombre)
                if match:
                    detalle_choferes[nombre] = {
                        "total": int(grupo["Total"].sum()),
                        "entregadas": int(grupo["Entregadas"].sum()),
                        "pendientes": int(grupo["Pendientes"].sum()),
                        "hrs": len(grupo)
                    }

            historico[fecha_archivo] = {
                "choferes_pendientes": choferes_pend,
                "hdr_pendientes": hdr_pendientes,
                "total": int(total_total),
                "entregadas": int(total_entregadas),
                "pct_entregado": pct_entregado,
                "detalle": detalle_choferes
            }
            with open(HIST_FILE, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=2)
            st.caption(f"✅ Registro guardado para el {fecha_display}")

            st.write("---")

            # --- WhatsApp por chofer ---
            if df_pend.empty:
                st.success("✅ Sin hojas de ruta pendientes.")
            else:
                hoy = date.today().strftime("%d/%m/%Y")
                grupos = df_pend.groupby("Nombre_Chofer")
                encontrados, excluidos = [], []

                for nombre, grupo in grupos:
                    match = buscar_chofer(nombre)
                    if match:
                        encontrados.append((nombre, match[0], match[1], grupo))
                    else:
                        excluidos.append(nombre)

                st.markdown(f"### 📋 {len(encontrados)} chofer(es) con pendientes")
                if excluidos:
                    st.info(f"⚠️ Excluidos (no registrados): {', '.join(excluidos)}")

                for nombre_excel, nombre_registro, telefono, grupo in encontrados:
                    total_pend = grupo["Pendientes"].sum()
                    primer_nombre = nombre_registro.split()[0].title()

                    lineas = []
                    for _, row in grupo.iterrows():
                        zona = str(row["Nombre_Reparto"]).strip()
                        hr = int(row["Hoja_Ruta"]) if pd.notna(row["Hoja_Ruta"]) else "—"
                        lineas.append(f"  • HR {hr} | {zona}")
                    detalle = "\n".join(lineas)

                    mensaje = (
                        f"Hola {primer_nombre} 👋\n"
                        f"Resumen de Hojas de Ruta pendientes al {fecha_display}:\n\n"
                        f"{detalle}\n\n"
                        f"Por favor confirmá recepción. Gracias! 🚛\n— INNER LOGISTICS"
                    )

                    wa_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(mensaje)}"
                    with st.expander(f"🚛 {nombre_excel}  |  {total_pend} HR(s) pendiente(s)"):
                        st.text_area("Mensaje:", mensaje, height=160, key=f"msg_{nombre_excel}")
                        st.link_button("📲 Enviar por WhatsApp", wa_url, use_container_width=True)

    # --- Botón Dashboard + Sección histórico KPI ---
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 VER DASHBOARD COMPLETO", use_container_width=True, key="btn_dashboard"):
            st.session_state.show_dashboard = not st.session_state.get("show_dashboard", False)

        if st.session_state.get("show_dashboard", False):
            import streamlit.components.v1 as components
            import json
            from datetime import datetime as _dt
            # Botón pantalla completa — expande el iframe via JS
            st.markdown("""
                <button onclick="
                    const iframe = window.parent.document.querySelector('iframe[title=\"st.components.v1.html\"]');
                    if(iframe){
                        if(iframe.requestFullscreen) iframe.requestFullscreen();
                        else if(iframe.webkitRequestFullscreen) iframe.webkitRequestFullscreen();
                        else if(iframe.mozRequestFullScreen) iframe.mozRequestFullScreen();
                    }
                " style="
                    margin-bottom:8px; padding:7px 16px;
                    background:transparent; border:1px solid #FACC15; color:#FACC15;
                    border-radius:8px; font-weight:700; font-size:0.85rem;
                    cursor:pointer; font-family:sans-serif; letter-spacing:0.05em;
                ">⛶ Pantalla completa</button>
            """, unsafe_allow_html=True)
            HIST_FILE = "kpi_historico.json"
            dash_path = "dashboard.html"
            if not os.path.exists(HIST_FILE):
                st.warning("⚠️ Aún no hay historial generado. Cargá un Excel primero.")
            elif not os.path.exists(dash_path):
                st.error("⚠️ Archivo dashboard.html no encontrado en la carpeta del proyecto.")
            else:
                with open(HIST_FILE, "r", encoding="utf-8") as f:
                    hist_data = json.load(f)
                with open(dash_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Determinar fecha seleccionada en el calendario histórico
                fecha_dash = st.session_state.get("hist_fecha", None)
                if fecha_dash:
                    fecha_key_dash = fecha_dash.strftime("%Y-%m-%d")
                else:
                    fecha_key_dash = sorted(hist_data.keys())[-1]

                # Inyectar historial completo + fecha seleccionada en el HTML
                inject = f"""
                <script>
                  window._HISTORICO = {json.dumps(hist_data)};
                  window._FECHA_INICIAL = "{fecha_key_dash}";
                </script>
                """
                # Reemplazar el bloque de demo data por los datos reales
                html_content = html_content.replace("</head>", inject + "</head>")
                components.html(html_content, height=920, scrolling=True)

    # --- Sección histórico KPI (siempre visible bajo LOG-IN) ---
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📅 Historial KPI")
        HIST_FILE = "kpi_historico.json"
        if not os.path.exists(HIST_FILE):
            st.caption("Aún no hay registros históricos. Cargá un Excel para comenzar.")
        else:
            import json
            from datetime import datetime
            with open(HIST_FILE, "r", encoding="utf-8") as f:
                historico = json.load(f)

            fechas_disponibles = sorted(historico.keys(), reverse=True)
            fechas_dt = [datetime.strptime(f, "%Y-%m-%d").date() for f in fechas_disponibles]

            fecha_sel = st.date_input(
                "Seleccioná una fecha:",
                value=fechas_dt[0],
                min_value=fechas_dt[-1],
                max_value=fechas_dt[0],
                key="hist_fecha"
            )
            fecha_key = fecha_sel.strftime("%Y-%m-%d")
            if fecha_key in historico:
                reg = historico[fecha_key]
                fd = fecha_sel.strftime("%d/%m/%Y")
                st.markdown(f"#### Resumen del {fd}")
                _pct_h = reg["pct_entregado"]
                _color_pct_h = "#4ADE80" if _pct_h >= 90 else "#F87171"
                st.markdown(f"""
                    <div style='display:flex; gap:12px; margin:10px 0;'>
                        <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                    border-radius:12px; padding:16px 10px; text-align:center;'>
                            <div style='font-size:40px; font-weight:900; color:white; line-height:1'>{reg["choferes_pendientes"]}</div>
                            <div style='color:#ccc; font-size:0.78rem; margin-top:4px;'>Choferes c/ pendientes</div>
                        </div>
                        <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                    border-radius:12px; padding:16px 10px; text-align:center;'>
                            <div style='font-size:40px; font-weight:900; color:white; line-height:1'>{reg["hdr_pendientes"]}</div>
                            <div style='color:#ccc; font-size:0.78rem; margin-top:4px;'>HRs pendientes</div>
                        </div>
                        <div style='flex:1; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.2);
                                    border-radius:12px; padding:16px 10px; text-align:center;'>
                            <div style='font-size:40px; font-weight:900; color:{_color_pct_h}; line-height:1'>{_pct_h}%</div>
                            <div style='color:#ccc; font-size:0.78rem; margin-top:4px;'>% Entregado</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if reg.get("detalle"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**Detalle por chofer:**")
                    import pandas as pd
                    rows = []
                    for nombre, d in reg["detalle"].items():
                        pct = round(d["entregadas"] / d["total"] * 100, 1) if d["total"] > 0 else 0
                        rows.append({
                            "Chofer": nombre,
                            "HRs": d["hrs"],
                            "Total": d["total"],
                            "Entregadas": d["entregadas"],
                            "Pendientes": d["pendientes"],
                            "% Entregado": f"{pct}%"
                        })
                    df_hist = pd.DataFrame(rows)
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)

                    # Exportar a Excel
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        # Hoja resumen
                        resumen = pd.DataFrame([{
                            "Fecha": fd,
                            "Choferes con pendientes": reg["choferes_pendientes"],
                            "HRs pendientes": reg["hdr_pendientes"],
                            "Total entregas": reg["total"],
                            "Entregadas": reg["entregadas"],
                            "% Entregado": f"{reg['pct_entregado']}%"
                        }])
                        resumen.to_excel(writer, sheet_name="Resumen KPI", index=False)
                        df_hist.to_excel(writer, sheet_name="Detalle por Chofer", index=False)
                    buf.seek(0)
                    st.download_button(
                        label="📥 Descargar KPI en Excel",
                        data=buf,
                        file_name=f"KPI_{fecha_key.replace('-','')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.warning(f"No hay registro para {fecha_sel.strftime('%d/%m/%Y')}. Seleccioná otra fecha.")

    with col2:
        app_card("logo_beetrack.png", None, "BEETRACK")
        st.markdown("""
            <div style='text-align:center; margin-top:10px; padding:8px 12px;
                        background:rgba(255,255,255,0.04); border-radius:10px;
                        border:1px solid rgba(255,255,255,0.08);'>
                <span style='color:#64748b; font-size:0.8rem;'>🚧 Página en desarrollo</span>
            </div>""", unsafe_allow_html=True)
    with col3:
        app_card("logo_dt.png", None, "DISPATCH TRACK")
        st.markdown("""
            <div style='text-align:center; margin-top:10px; padding:8px 12px;
                        background:rgba(255,255,255,0.04); border-radius:10px;
                        border:1px solid rgba(255,255,255,0.08);'>
                <span style='color:#64748b; font-size:0.8rem;'>🚧 Página en desarrollo</span>
            </div>""", unsafe_allow_html=True)
