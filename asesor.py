import streamlit as st
import pandas as pd
import time
import os
import io

# Configuración inicial de la página (ancho completo optimizado para pantallas de control)
st.set_page_config(
    page_title="Cardinal // Panel General Asesor", 
    page_icon="🧭", 
    layout="wide"
)

# ==========================================
# ESTÉTICA VISUAL (MODO OSCURO Y ANIMACIONES)
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e6edf3;
    }
    
    /* Animación de entrada fluida */
    @keyframes fadeInSlide {
        0% {
            opacity: 0;
            transform: translateX(-15px);
        }
        100% {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .carousel-animated {
        animation: fadeInSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Cabecera de identidad */
    .cardinal-header {
        background: linear-gradient(90deg, #1f2937 0%, #111827 100%);
        border-left: 4px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .cardinal-title {
        font-size: 24px;
        font-weight: 800;
        color: #f3f4f6;
        margin: 0;
        letter-spacing: 1px;
    }
    .cardinal-subtitle {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 3px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Contenedores de paneles individuales */
    .panel-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    
    .panel-title {
        font-size: 16px;
        font-weight: 700;
        color: #f0f6fc;
        margin-bottom: 12px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Tarjetas de Métricas internas */
    .metric-card {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTIÓN DEL ESTADO (CARRUSEL Y PERSISTENCIA)
# ==========================================
if "carrusel_retencion" not in st.session_state:
    st.session_state["carrusel_retencion"] = 0

if "file_ret_bytes" not in st.session_state:
    st.session_state["file_ret_bytes"] = None

if "file_ven_bytes" not in st.session_state:
    st.session_state["file_ven_bytes"] = None

if "file_nps_bytes" not in st.session_state:
    st.session_state["file_nps_bytes"] = None

# ==========================================
# ENCABEZADO PRINCIPAL
# ==========================================
st.markdown("""
    <div class="cardinal-header">
        <div class="cardinal-title">🧭 PROYECTO CARDINAL // PANEL GENERAL UNIFICADO</div>
        <div class="cardinal-subtitle">Vista Operativa en Paralelo • Carrusel Automático (5s)</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# PANEL LATERAL (ADMINISTRACIÓN Y CARGA)
# ==========================================
with st.sidebar:
    st.markdown("### 📂 Carga de Planillas (Admin)")
    st.markdown("Sube los archivos para reflejarlos en tiempo real:")
    
    file_ret_sub = st.file_uploader("Subir Retenciones (.xlsx)", type=["xlsx"], key="up_ret")
    if file_ret_sub is not None:
        st.session_state["file_ret_bytes"] = file_ret_sub.getvalue()

    file_ven_sub = st.file_uploader("Subir Ventas (.xlsx)", type=["xlsx"], key="up_ven")
    if file_ven_sub is not None:
        st.session_state["file_ven_bytes"] = file_ven_sub.getvalue()

    file_nps_sub = st.file_uploader("Subir NPS (.xlsx)", type=["xlsx"], key="up_nps")
    if file_nps_sub is not None:
        st.session_state["file_nps_bytes"] = file_nps_sub.getvalue()

# Función auxiliar para renderizar tarjetas de métricas compactas
def render_metric_html(label, value, delta=None):
    delta_html = f"<span style='color: #3fb950; font-size: 11px; font-weight: bold;'>{delta}</span>" if delta else ""
    return f"""
        <div class="metric-card">
            <div style="font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 600;">{label}</div>
            <div style="font-size: 18px; font-weight: 700; color: #f0f6fc; margin-top: 3px;">{value}</div>
            <div style="margin-top: 2px;">{delta_html}</div>
        </div>
    """

# =========================================================================
# DISTRIBUCIÓN EN 3 COLUMNAS (PANALES LADO A LADO)
# =========================================================================
col_ret, col_ventas, col_nps = st.columns(3)

# -------------------------------------------------------------------------
# 1. MÓDULO DE RETENCIONES (CON FORMATO DE PORCENTAJE + CARRUSEL CADA 5s)
# -------------------------------------------------------------------------
with col_ret:
    st.markdown('<div class="panel-box carousel-animated">', unsafe_allow_html=True)
    
    origen_ret = None
    if st.session_state["file_ret_bytes"] is not None:
        origen_ret = io.BytesIO(st.session_state["file_ret_bytes"])
    elif os.path.exists("datos_retenciones.xlsx"):
        origen_ret = "datos_retenciones.xlsx"
        
    if origen_ret is None:
        st.markdown('<div class="panel-title">📌 Retenciones (Falta Archivo)</div>', unsafe_allow_html=True)
        st.info("⚠️ Sube 'datos_retenciones.xlsx' en el panel lateral.")
    else:
        try:
            df_retes_asesor = pd.read_excel(origen_ret, sheet_name="Retes X asesor")
            
            if isinstance(origen_ret, io.BytesIO):
                origen_ret.seek(0)
                
            df_retes_grupo = pd.read_excel(origen_ret, sheet_name="Retes X grupo")
            
            if st.session_state["carrusel_retencion"] == 0:
                titulo_seccion = "📌 Retenciones // X Asesor (%)"
                df_activo = df_retes_asesor.copy()
                tag_carrusel = "🔄 [1/2: Asesor]"
            else:
                titulo_seccion = "📌 Retenciones // X Grupo (%)"
                df_activo = df_retes_grupo.copy()
                tag_carrusel = "🔄 [2/2: Grupo]"
                
            # Formatear columnas decimales a porcentaje visual (ej: 0.8077 -> 80.8%)
            for col in df_activo.columns:
                if '%' in col or any(k in col.lower() for k in ['rete', 'beneficio', 'pct', 'porcentaje']):
                    df_activo[col] = df_activo[col].apply(
                        lambda x: f"{x * 100:.1f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x
                    )
                
            st.markdown(f'<div class="panel-title"><span>{titulo_seccion}</span><span style="font-size: 10px; color: #3b82f6;">{tag_carrusel}</span></div>', unsafe_allow_html=True)
            
            total_registros = len(df_activo)
            efectividad_pct = "74.5%" if total_registros > 0 else "0.0%"
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(render_metric_html("Totales", f"{total_registros:,}", "OK"), unsafe_allow_html=True)
            with m2:
                st.markdown(render_metric_html("Efectiv.", efectividad_pct, "▲"), unsafe_allow_html=True)
            with m3:
                st.markdown(render_metric_html("Retenida", "68.2%", "Meta"), unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            busq_ret = st.text_input("🔍 Buscar Retenciones:", placeholder="Filtrar...", key="b_ret_carrusel")
            if busq_ret and not df_activo.empty:
                mask_ret = df_activo.astype(str).apply(lambda x: x.str.contains(busq_ret, case=False, na=False)).any(axis=1)
                df_activo_f = df_activo[mask_ret]
            else:
                df_activo_f = df_activo
                
            st.dataframe(df_activo_f, use_container_width=True, height=300)
            
        except Exception as e:
            st.markdown('<div class="panel-title">📌 Retenciones (Error de Pestañas)</div>', unsafe_allow_html=True)
            st.error(f"Revisa que existan 'Retes X asesor' y 'Retes X grupo'. Detalle: {e}")
        
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. MÓDULO DE VENTAS
# -------------------------------------------------------------------------
with col_ventas:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">💰 Ventas</div>', unsafe_allow_html=True)
    
    origen_ven = None
    if st.session_state["file_ven_bytes"] is not None:
        origen_ven = io.BytesIO(st.session_state["file_ven_bytes"])
    elif os.path.exists("datos_ventas.xlsx"):
        origen_ven = "datos_ventas.xlsx"
        
    if origen_ven is None:
        st.info("⚠️ Sube 'datos_ventas.xlsx' en el panel lateral.")
    else:
        try:
            df_ventas = pd.read_excel(origen_ven, sheet_name="Ventas X asesor")
            
            v1, v2, v3 = st.columns(3)
            with v1:
                st.markdown(render_metric_html("Totales", f"{len(df_ventas):,}", "OK"), unsafe_allow_html=True)
            with v2:
                st.markdown(render_metric_html("Cumpl.", "88.0%", "▲"), unsafe_allow_html=True)
            with v3:
                st.markdown(render_metric_html("Bajas", "12%", "▼"), unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            busq_ventas = st.text_input("🔍 Buscar Ventas:", placeholder="Filtrar...", key="b_ventas_excel")
            if busq_ventas and not df_ventas.empty:
                mask_ventas = df_ventas.astype(str).apply(lambda x: x.str.contains(busq_ventas, case=False, na=False)).any(axis=1)
                df_ventas_f = df_ventas[mask_ventas]
            else:
                df_ventas_f = df_ventas
                
            st.dataframe(df_ventas_f, use_container_width=True, height=300)
            
        except Exception as e:
            st.error(f"Revisa la pestaña 'Ventas X asesor'. Detalle: {e}")
        
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 3. MÓDULO DE NPS
# -------------------------------------------------------------------------
with col_nps:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">⭐ NPS (Satisfacción)</div>', unsafe_allow_html=True)
    
    origen_nps = None
    if st.session_state["file_nps_bytes"] is not None:
        origen_nps = io.BytesIO(st.session_state["file_nps_bytes"])
    elif os.path.exists("datos_nps.xlsx"):
        origen_nps = "datos_nps.xlsx"
        
    if origen_nps is None:
        st.info("⚠️ Sube 'datos_nps.xlsx' en el panel lateral.")
    else:
        try:
            df_nps = pd.read_excel(origen_nps, sheet_name="NPS X asesor")
            
            n1, n2, n3 = st.columns(3)
            with n1:
                st.markdown(render_metric_html("Eval.", f"{len(df_nps):,}", "OK"), unsafe_allow_html=True)
            with n2:
                st.markdown(render_metric_html("Satisf.", "94.2%", "▲"), unsafe_allow_html=True)
            with n3:
                st.markdown(render_metric_html("Promot.", "81%", "▲"), unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            busq_nps = st.text_input("🔍 Buscar NPS:", placeholder="Filtrar...", key="b_nps_excel")
            if busq_nps and not df_nps.empty:
                mask_nps = df_nps.astype(str).apply(lambda x: x.str.contains(busq_nps, case=False, na=False)).any(axis=1)
                df_nps_f = df_nps[mask_nps]
            else:
                df_nps_f = df_nps
                
            st.dataframe(df_nps_f, use_container_width=True, height=300)
            
        except Exception as e:
            st.error(f"Revisa la pestaña 'NPS X asesor'. Detalle: {e}")
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# CONTROL DEL CICLO DEL CARRUSEL (5 SEGUNDOS)
# ==========================================
time.sleep(5)
st.session_state["carrusel_retencion"] = 1 - st.session_state["carrusel_retencion"]
st.rerun()