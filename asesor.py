import streamlit as st
import pandas as pd
import time
import os
import io
import calendar
from datetime import datetime

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
        margin-bottom: 20px;
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

if "file_asistencias_bytes" not in st.session_state:
    st.session_state["file_asistencias_bytes"] = None

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

    file_asis_sub = st.file_uploader("Subir Asistencias (.xlsx)", type=["xlsx"], key="up_asis")
    if file_asis_sub is not None:
        st.session_state["file_asistencias_bytes"] = file_asis_sub.getvalue()

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
# 1. MÓDULO DE RETENCIONES
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


# =========================================================================
# MÓDULO: CALENDARIO DE ASISTENCIA PERSONAL (VISTA ASESOR)
# =========================================================================
st.markdown('<div class="panel-box">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">📅 Mi Historial de Asistencia Mensual</div>', unsafe_allow_html=True)

col_asesor_sel, col_mes_sel = st.columns([2, 2])

with col_asesor_sel:
    nombre_asesor = st.text_input("👤 Tu Nombre / Usuario de Asesor:", value="Erika Aguirre", placeholder="Ingresa tu nombre...", key="input_nombre_asesor")

with col_mes_sel:
    meses_nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    mes_actual_num = datetime.now().month
    anio_actual = datetime.now().year
    
    mes_elegido_nombre = st.selectbox("📆 Seleccionar Mes:", list(meses_nombres.values()), index=mes_actual_num - 1, key="select_mes_calendario")
    mes_elegido_num = [k for k, v in meses_nombres.items() if v == mes_elegido_nombre][0]

origen_asis = None
if st.session_state["file_asistencias_bytes"] is not None:
    origen_asis = io.BytesIO(st.session_state["file_asistencias_bytes"])
elif os.path.exists("datos_asistencias.xlsx"):
    origen_asis = "datos_asistencias.xlsx"

if origen_asis is None:
    st.info("⚠️ Aún no se cargó el archivo 'datos_asistencias.xlsx'. Súbelo desde el panel lateral para ver tu calendario.")
else:
    try:
        df_asistencias = pd.read_excel(origen_asis)
        
        col_fecha = next((c for c in df_asistencias.columns if 'fecha' in c.lower()), None)
        col_asesor = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['asesor', 'agente', 'nombre', 'usuario'])), None)
        col_estado = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['estado', 'asistencia', 'tipo'])), None)
        col_motivo = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['motivo', 'observacion', 'comentario', 'detalle'])), None)
        
        if not col_fecha or not col_asesor:
            st.warning("⚠️ El archivo de asistencias no tiene las columnas reconocibles ('Fecha', 'Asesor').")
        else:
            df_asistencias[col_fecha] = pd.to_datetime(df_asistencias[col_fecha], errors='coerce')
            
            mask_asesor = df_asistencias[col_asesor].astype(str).str.contains(nombre_asesor, case=False, na=False)
            mask_mes = (df_asistencias[col_fecha].dt.month == mes_elegido_num) & (df_asistencias[col_fecha].dt.year == anio_actual)
            
            df_mi_mes = df_asistencias[mask_asesor & mask_mes].copy()
            
            registro_dias = {}
            for _, row in df_mi_mes.iterrows():
                f_obj = row[col_fecha]
                if pd.notnull(f_obj):
                    dia_num = f_obj.day
                    estado = str(row[col_estado]).strip().lower() if col_estado and pd.notnull(row[col_estado]) else "presente"
                    motivo = str(row[col_motivo]).strip() if col_motivo and pd.notnull(row[col_motivo]) else ""
                    registro_dias[dia_num] = {"estado": estado, "motivo": motivo}

            st.markdown("""
                <div style="display: flex; gap: 15px; margin-bottom: 15px; font-size: 12px; align-items: center;">
                    <span><b>Referencias:</b></span>
                    <span style="background: #238636; padding: 3px 8px; border-radius: 4px; color: white;">🟢 Presente</span>
                    <span style="background: #da3633; padding: 3px 8px; border-radius: 4px; color: white;">🔴 Ausente</span>
                    <span style="background: #9e6a03; padding: 3px 8px; border-radius: 4px; color: white;">🟡 Novedad / Observación</span>
                </div>
            """, unsafe_allow_html=True)

            cal = calendar.monthcalendar(anio_actual, mes_elegido_num)
            dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            
            cols_sem = st.columns(7)
            for i, d_sem in enumerate(dias_semana):
                cols_sem[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #8b949e; font-size: 12px;'>{d_sem}</div>", unsafe_allow_html=True)

            for semana in cal:
                cols_dias = st.columns(7)
                for i, dia_num in enumerate(semana):
                    with cols_dias[i]:
                        if dia_num == 0:
                            st.markdown("<div style='padding: 10px;'></div>", unsafe_allow_html=True)
                        else:
                            info_dia = registro_dias.get(dia_num, None)
                            bg_color, border_col, emoji_estado = "#21262d", "#30363d", ""
                            
                            if info_dia:
                                est, mot = info_dia["estado"], info_dia["motivo"]
                                if any(k in est for k in ['ausente', 'falta', 'injustificado']):
                                    bg_color, border_col, emoji_estado = "#5a1d1d", "#da3633", "🔴"
                                elif mot and len(mot) > 2:
                                    bg_color, border_col, emoji_estado = "#4d3800", "#bb8009", "🟡"
                                else:
                                    bg_color, border_col, emoji_estado = "#113822", "#238636", "🟢"

                            st.markdown(f"""
                                <div style="background-color: {bg_color}; border: 1px solid {border_col}; border-radius: 6px; padding: 8px; text-align: center; min-height: 50px; margin-bottom: 5px;">
                                    <div style="font-size: 14px; font-weight: bold; color: #f0f6fc;">{dia_num}</div>
                                    <div style="font-size: 11px; margin-top: 2px;">{emoji_estado}</div>
                                </div>
                            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            max_dias = calendar.monthrange(anio_actual, mes_elegido_num)[1]
            dia_seleccionado = st.selectbox("🔍 Selecciona un día del mes para ver el detalle de la supervisora:", [d for d in range(1, max_dias + 1)], key="sel_dia_asis")
            
            if dia_seleccionado in registro_dias:
                detalle = registro_dias[dia_seleccionado]
                st.info(f"📝 **Detalle para el día {dia_seleccionado} de {mes_elegido_nombre}:**\n\n- **Estado registrado:** {detalle['estado'].capitalize()}\n- **Observación de la supervisora:** {detalle['motivo'] if detalle['motivo'] else 'Sin observaciones adicionales.'}")
            else:
                st.success(f"✅ Día {dia_seleccionado} de {mes_elegido_nombre}: Sin registros particulares cargados o figurás presente con normalidad.")

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo de asistencias para el calendario. Detalle: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# CONTROL DEL CICLO DEL CARRUSEL (5 SEGUNDOS)
# ==========================================
time.sleep(5)
st.session_state["carrusel_retencion"] = 1 - st.session_state["carrusel_retencion"]
st.rerun()