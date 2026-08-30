import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime

def mostrar_calendario_asesor():
    st.markdown("""
        <div style="background: linear-gradient(90deg, #1f2937 0%, #111827 100%); border-left: 4px solid #3b82f6; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #f3f4f6; margin: 0;">📅 Mi Calendario de Asistencia Mensual</h2>
            <p style="color: #9ca3af; margin: 3px 0 0 0; font-size: 12px; text-transform: uppercase;">Control de presencias, ausencias y novedades de supervisión</p>
        </div>
    """, unsafe_allow_html=True)

    col_mes_sel, col_vacio = st.columns([2, 2])
    with col_mes_sel:
        meses_nombres = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        mes_actual_num = datetime.now().month
        anio_actual = datetime.now().year
        
        mes_elegido_nombre = st.selectbox("📆 Seleccionar Mes a Consultar:", list(meses_nombres.values()), index=mes_actual_num - 1, key="sel_mes_calendario")
        mes_elegido_num = [k for k, v in meses_nombres.items() if v == mes_elegido_nombre][0]

    # Tomamos el usuario logueado en la sesión
    usuario_actual = st.session_state.get('usuario', 'AGUIRRE ERIKA')

    origen_asis = "datos_asistencias.xlsx" if os.path.exists("datos_asistencias.xlsx") else None

    if not origen_asis:
        st.warning("⚠️ Aún no se encuentra el archivo 'datos_asistencias.xlsx' en el directorio del proyecto.")
        return

    try:
        df_asistencias = pd.read_excel(origen_asis)
        
        col_fecha = next((c for c in df_asistencias.columns if 'fecha' in c.lower()), None)
        col_asesor = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['asesor', 'agente', 'nombre', 'usuario'])), None)
        col_estado = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['estado', 'asistencia', 'tipo'])), None)
        col_motivo = next((c for c in df_asistencias.columns if any(k in c.lower() for k in ['motivo', 'observacion', 'comentario', 'detalle'])), None)
        
        if not col_fecha or not col_asesor:
            st.error("⚠️ El archivo de asistencias no contiene las columnas necesarias ('Fecha' y 'Asesor').")
            return

        df_asistencias[col_fecha] = pd.to_datetime(df_asistencias[col_fecha], errors='coerce')
        
        mask_asesor = df_asistencias[col_asesor].astype(str).str.contains(usuario_actual, case=False, na=False)
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

        # Leyenda de referencias
        st.markdown("""
            <div style="display: flex; gap: 15px; margin: 15px 0; font-size: 12px; align-items: center;">
                <span><b>Referencias:</b></span>
                <span style="background: #238636; padding: 3px 8px; border-radius: 4px; color: white;">🟢 Presente</span>
                <span style="background: #da3633; padding: 3px 8px; border-radius: 4px; color: white;">🔴 Ausente</span>
                <span style="background: #9e6a03; padding: 3px 8px; border-radius: 4px; color: white;">🟡 Novedad / Observación</span>
            </div>
        """, unsafe_allow_html=True)

        # Dibujar la estructura del calendario mensual
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

        # Detalle interactivo del día seleccionado
        st.markdown("<br>", unsafe_allow_html=True)
        max_dia = calendar.monthrange(anio_actual, mes_elegido_num)[1]
        dia_seleccionado = st.selectbox("🔍 Selecciona un día para ver el detalle de supervisión:", [d for d in range(1, max_dia + 1)], key="sel_dia_interactivo")
        
        if dia_seleccionado in registro_dias:
            detalle = registro_dias[dia_seleccionado]
            st.info(f"📝 **Detalle del día {dia_seleccionado} de {mes_elegido_nombre}:**\n\n- **Estado:** {detalle['estado'].capitalize()}\n- **Observación:** {detalle['motivo'] if detalle['motivo'] else 'Sin observaciones adicionales.'}")
        else:
            st.success(f"✅ Día {dia_seleccionado} de {mes_elegido_nombre}: Sin novedades particulares registradas.")

    except Exception as e:
        st.error(f"⚠️ Error al procesar las asistencias: {e}")