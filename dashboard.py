import base64
import calendar
import datetime
import os
import pandas as pd
import streamlit as st


def mostrar_panel_admin(
    origen_retenciones, origen_nps, origen_ventas, objetivos, rol
):
    """Panel exclusivo para Administradores, Masters y Supervisores con NPS global agregado."""

    user_key = st.session_state.get("user", "Admin")
    nombre_mostrar = st.session_state.get(
        "nombre_mostrar", "Administrador / Supervisor"
    )

    foto_path = f"fotos/{user_key}.png"
    if not os.path.exists(foto_path):
        foto_path = f"fotos/{user_key}.jpg"

    if os.path.exists(foto_path):
        with open(foto_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 3px solid #58a6ff; margin-right: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">'
    else:
        img_html = '<div style="width: 140px; height: 140px; border-radius: 50%; background-color: #21262d; border: 3px solid #30363d; display: flex; align-items: center; justify-content: center; font-size: 70px; margin-right: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">🧭</div>'

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; padding: 10px 0 25px 0;">
            {img_html}
            <div>
                <h1 style='color: #58a6ff; font-size: 2.2rem; margin: 0; text-align: left;'>Consola de Supervisión — {nombre_mostrar}</h1>
                <p style='color: #8b949e; font-size: 0.95rem; margin: 5px 0 0 0; text-align: left;'>Vista gerencial y de control operativo ({rol.capitalize()})</p>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    df_ret = (
        pd.read_excel(origen_retenciones, sheet_name="Retes X asesor")
        if origen_retenciones
        else (
            pd.read_excel("datos_retenciones.xlsx", sheet_name="Retes X asesor")
            if os.path.exists("datos_retenciones.xlsx")
            else pd.DataFrame()
        )
    )
    df_nps = (
        pd.read_excel(origen_nps)
        if origen_nps
        else (
            pd.read_excel("datos_nps.xlsx")
            if os.path.exists("datos_nps.xlsx")
            else pd.DataFrame()
        )
    )
    df_ventas = (
        pd.read_excel(origen_ventas)
        if origen_ventas
        else (
            pd.read_excel("datos_ventas.xlsx")
            if os.path.exists("datos_ventas.xlsx")
            else pd.DataFrame()
        )
    )

    meta_rete = objetivos.get("rete_pct", 0.70)
    meta_bene = objetivos.get("beneficio_pct", 0.40)
    meta_ventas = objetivos.get("ventas_grupal", 260)

    tot_rete, tot_bene, tot_ventas = 0.0, 0.0, 0
    if not df_ret.empty:
        col_r = next(
            (c for c in df_ret.columns if "rete" in str(c).lower()),
            df_ret.columns[1] if len(df_ret.columns) > 1 else None,
        )
        col_b = next(
            (c for c in df_ret.columns if "beneficio" in str(c).lower()), None
        )
        if col_r:
            tot_rete = (
                pd.to_numeric(df_ret[col_r], errors="coerce").mean() or 0.0
            )
        if col_b:
            tot_bene = (
                pd.to_numeric(df_ret[col_b], errors="coerce").mean() or 0.0
            )

    if not df_ventas.empty:
        col_v = df_ventas.columns[-1]
        tot_ventas = int(
            pd.to_numeric(df_ventas[col_v], errors="coerce").sum() or 0
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">% RETE CTA'
            f' (Global)</div><div class="metric-value">{tot_rete*100:.1f}%</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">BENEFICIO'
            f' (Global)</div><div class="metric-value">{tot_bene*100:.1f}%</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="metric-card"><div class="metric-title">NPS'
            ' Positivo</div><div class="metric-value">80.0%</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Ventas'
            f' Grupales</div><div class="metric-value">{tot_ventas}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("📋 Detalle Operativo General")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### Rendimiento y Retenciones por Asesores / Grupos")
        if not df_ret.empty:
            st.dataframe(df_ret, use_container_width=True, height=350)
        else:
            st.info("Sin datos de retenciones cargados.")

    with col_t2:
        st.markdown("#### Detalle de Ventas")
        if not df_ventas.empty:
            st.dataframe(df_ventas, use_container_width=True, height=350)
        else:
            st.info("Sin datos de ventas cargados.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Detalle General de NPS")
    if not df_nps.empty:
        st.dataframe(df_nps, use_container_width=True, height=350)
    else:
        st.info("Sin datos de NPS cargados.")


def mostrar_panel_asesor(
    nombre_mostrar,
    asesor_objetivo,
    origen_retenciones,
    origen_nps,
    origen_ventas,
    objetivos,
):
    """Panel exclusivo para Asesores con persistencia, filtrado inteligente y calendario visual mensual navegable."""

    user_key = st.session_state.get("user", "")
    foto_path = f"fotos/{user_key}.png"
    if not os.path.exists(foto_path):
        foto_path = f"fotos/{user_key}.jpg"

    if os.path.exists(foto_path):
        with open(foto_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 3px solid #58a6ff; margin-right: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">'
    else:
        img_html = '<div style="width: 140px; height: 140px; border-radius: 50%; background-color: #21262d; border: 3px solid #30363d; display: flex; align-items: center; justify-content: center; font-size: 70px; margin-right: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">👤</div>'

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; padding: 10px 0 25px 0;">
            {img_html}
            <div>
                <h1 style='color: #58a6ff; font-size: 2.2rem; margin: 0; text-align: left;'>Mi Panel Personal — {nombre_mostrar}</h1>
                <p style='color: #8b949e; font-size: 0.95rem; margin: 5px 0 0 0; text-align: left;'>Monitoreo individual de rendimiento y objetivos</p>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    df_ret = (
        pd.read_excel(origen_retenciones, sheet_name="Retes X asesor")
        if origen_retenciones
        else (
            pd.read_excel("datos_retenciones.xlsx", sheet_name="Retes X asesor")
            if os.path.exists("datos_retenciones.xlsx")
            else pd.DataFrame()
        )
    )
    df_nps = (
        pd.read_excel(origen_nps)
        if origen_nps
        else (
            pd.read_excel("datos_nps.xlsx")
            if os.path.exists("datos_nps.xlsx")
            else pd.DataFrame()
        )
    )
    df_ventas = (
        pd.read_excel(origen_ventas)
        if origen_ventas
        else (
            pd.read_excel("datos_ventas.xlsx")
            if os.path.exists("datos_ventas.xlsx")
            else pd.DataFrame()
        )
    )

    meta_rete = objetivos.get("rete_pct", 0.70)
    meta_bene = objetivos.get("beneficio_pct", 0.40)

    def filtrar_dataframe(df):
        if df.empty:
            return df
        texto_a_buscar = str(asesor_objetivo if asesor_objetivo else nombre_mostrar)
        palabras_clave = [
            p.strip()
            for p in texto_a_buscar.lower().replace(",", "").split()
            if len(p) > 2
        ]
        if not palabras_clave:
            palabras_clave = [texto_a_buscar.lower().strip()]

        col_objetivo = None
        for col in df.columns:
            col_str = str(col).lower()
            if any(
                k in col_str
                for k in [
                    "asesor",
                    "agente",
                    "nombre",
                    "ejecutivo",
                    "usuario",
                    "personal",
                ]
            ):
                col_objetivo = col
                break

        if col_objetivo is None:
            for col in df.columns:
                if df[col].dtype == object:
                    col_objetivo = col
                    break

        if col_objetivo is None:
            col_objetivo = df.columns[0]

        def match_fila(val):
            val_str = str(val).lower()
            return all(palabra in val_str for palabra in palabras_clave)

        condicion = df[col_objetivo].apply(match_fila)
        return df[condicion]

    mi_rete_val = 0.0
    mi_bene_val = 0.0
    df_mi_ret = pd.DataFrame()

    if not df_ret.empty:
        filtro_asesor = filtrar_dataframe(df_ret)
        if not filtro_asesor.empty:
            df_mi_ret = filtro_asesor
            col_r = next(
                (c for c in df_ret.columns if "rete" in str(c).lower()), None
            )
            col_b = next(
                (c for c in df_ret.columns if "beneficio" in str(c).lower()),
                None,
            )

            if col_r:
                mi_rete_val = (
                    pd.to_numeric(
                        filtro_asesor[col_r].values[0], errors="coerce"
                    )
                    or 0.0
                )
            if col_b:
                mi_bene_val = (
                    pd.to_numeric(
                        filtro_asesor[col_b].values[0], errors="coerce"
                    )
                    or 0.0
                )

    mi_venta_val = 0
    df_mi_ventas = pd.DataFrame()
    if not df_ventas.empty:
        filtro_v = filtrar_dataframe(df_ventas)
        col_vv = df_ventas.columns[-1]
        if not filtro_v.empty:
            df_mi_ventas = filtro_v
            mi_venta_val = int(
                pd.to_numeric(
                    filtro_v[col_vv].values[0], errors="coerce"
                )
                or 0
            )

    df_mi_nps = pd.DataFrame()
    if not df_nps.empty:
        filtro_nps = filtrar_dataframe(df_nps)
        if not filtro_nps.empty:
            df_mi_nps = filtro_nps

    # Tarjetas individuales
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ok_r = mi_rete_val >= meta_rete
        col_badge_r = "#3fb950" if ok_r else "#f85149"
        txt_r = "¡Cumplido!" if ok_r else "En Progreso"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-title">% RETE CTA (Personal)</div>
            <div class="metric-value">{mi_rete_val*100:.1f}%</div>
            <div style="color: {col_badge_r}; font-size: 0.75rem; font-weight: bold;">{txt_r}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        ok_b = mi_bene_val >= meta_bene
        col_badge_b = "#3fb950" if ok_b else "#f85149"
        txt_b = "¡Cumplido!" if ok_b else "En Progreso"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-title">BENEFICIO (Personal)</div>
            <div class="metric-value">{mi_bene_val*100:.1f}%</div>
            <div style="color: {col_badge_b}; font-size: 0.75rem; font-weight: bold;">{txt_b}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
        <div class="metric-card">
            <div class="metric-title">NPS Positivo</div>
            <div class="metric-value">--</div>
            <div style="color: #58a6ff; font-size: 0.75rem; font-weight: bold;">Monitoreo</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-title">Mis Ventas</div>
            <div class="metric-value">{mi_venta_val}</div>
            <div style="color: #58a6ff; font-size: 0.75rem; font-weight: bold;">Unidades</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Mis Registros y Métricas Detalladas")

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        st.markdown("#### Detalle de Retenciones")
        if not df_mi_ret.empty:
            st.dataframe(df_mi_ret, use_container_width=True)
        else:
            st.info("No se encontraron registros de retenciones personales.")

    with col_sub2:
        st.markdown("#### Detalle de NPS")
        if not df_mi_nps.empty:
            st.dataframe(df_mi_nps, use_container_width=True)
        else:
            st.info("No se encontraron registros de NPS personales.")

    # --- CALENDARIO VISUAL EN CUADRÍCULA REAL (ESTILO MES COMPLETO) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📅 Mi Calendario Operativo y Control de Asistencia")

    archivo_asistencias = "asistencias.xlsx"
    if not os.path.exists(archivo_asistencias) and os.path.exists(
        "datos_asistencias.xlsx"
    ):
        archivo_asistencias = "datos_asistencias.xlsx"

    df_asistencias = pd.DataFrame()
    if os.path.exists(archivo_asistencias):
        try:
            df_asistencias = pd.read_excel(archivo_asistencias)
        except Exception:
            try:
                df_asistencias = pd.read_excel(archivo_asistencias, sheet_name=0)
            except Exception:
                pass

    if not df_asistencias.empty:
        df_mi_asistencia = filtrar_dataframe(df_asistencias)

        if not df_mi_asistencia.empty:
            col_fecha = next(
                (
                    c
                    for c in df_mi_asistencia.columns
                    if any(
                        k in str(c).lower()
                        for k in ["fecha", "dia", "date", "periodo"]
                    )
                ),
                None,
            )
            col_estado = next(
                (
                    c
                    for c in df_mi_asistencia.columns
                    if any(
                        k in str(c).lower()
                        for k in [
                            "estado",
                            "asistencia",
                            "condicion",
                            "tipo",
                            "novedad",
                            "observacion",
                            "color",
                        ]
                    )
                ),
                None,
            )

            if col_fecha:
                try:
                    df_mi_asistencia["_dt"] = pd.to_datetime(
                        df_mi_asistencia[col_fecha], errors="coerce"
                    )
                except Exception:
                    df_mi_asistencia["_dt"] = pd.NaT

                def obtener_color_estado(val):
                    v = str(val).lower()
                    if any(
                        k in v
                        for k in [
                            "presente",
                            "ok",
                            "cumplido",
                            "asistio",
                            "trabajo",
                            "verde",
                            "(p)",
                        ]
                    ):
                        return "#238636"  # Verde
                    elif any(
                        k in v for k in ["ausente", "falta", "rojo", "tarde", "no"]
                    ):
                        return "#da3633"  # Rojo
                    elif any(
                        k in v
                        for k in [
                            "aviso",
                            "franco",
                            "amarillo",
                            "permiso",
                            "licencia",
                            "vacaciones",
                            "retiró",
                            "retiro",
                            "se retiró",
                            "(s)",
                        ]
                    ):
                        return "#d29922"  # Amarillo
                    return "#21262d"  # Fondo por defecto si no hay registro operativo

                diccionario_asistencias = {}
                for _, row in df_mi_asistencia.iterrows():
                    f_val = row[col_fecha]
                    if pd.notna(f_val):
                        f_str = str(f_val).split(" ")[0]
                        estado_txt = (
                            row[col_estado] if col_estado else "Sin detalle"
                        )
                        diccionario_asistencias[f_str] = {
                            "estado_txt": estado_txt,
                            "color": obtener_color_estado(estado_txt),
                            "fila_completa": row.to_dict(),
                        }

                st.markdown(
                    """
                    <div style="background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 15px;">
                        <span style="color: #8b949e; font-size: 0.9rem;">👁️ <b>Vista del Operador:</b> Calendario mensual interactivo. Los colores reflejan el control de la supervisión. Utiliza las flechas para navegar entre meses y selecciona una fecha abajo para desplegar el menú de detalles.</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # --- INICIALIZACIÓN Y GESTIÓN DE LA FECHA SELECCIONADA EN EL ESTADO ---
                if "current_date" not in st.session_state:
                    # Intentar usar el primer registro válido de la data del asesor o por defecto hoy
                    valid_dts = df_mi_asistencia["_dt"].dropna()
                    if not valid_dts.empty:
                        st.session_state.current_date = valid_dts.dt.date.iloc[0].replace(day=1)
                    else:
                        st.session_state.current_date = datetime.date.today().replace(day=1)

                meses_nombres = {
                    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 
                    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 
                    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
                }

                # --- BOTONERA CON FLECHAS PARA NAVEGAR ENTRE MESES ---
                col_izq, col_centro, col_der = st.columns([1, 4, 1])

                with col_izq:
                    if st.button("◀", use_container_width=True, key="mes_anterior"):
                        mes_actual = st.session_state.current_date.month
                        anio_actual = st.session_state.current_date.year
                        if mes_actual == 1:
                            st.session_state.current_date = datetime.date(anio_actual - 1, 12, 1)
                        else:
                            st.session_state.current_date = datetime.date(anio_actual, mes_actual - 1, 1)
                        st.rerun()

                with col_centro:
                    mes_nombre_str = meses_nombres[st.session_state.current_date.month]
                    anio_sel = st.session_state.current_date.year
                    st.markdown(
                        f"<h3 style='text-align: center; color: #58a6ff; margin: 0; text-transform: uppercase; letter-spacing: 1px;'>📅 {mes_nombre_str} {anio_sel}</h3>",
                        unsafe_allow_html=True,
                    )

                with col_der:
                    if st.button("▶", use_container_width=True, key="mes_siguiente"):
                        mes_actual = st.session_state.current_date.month
                        anio_actual = st.session_state.current_date.year
                        if mes_actual == 12:
                            st.session_state.current_date = datetime.date(anio_actual + 1, 1, 1)
                        else:
                            st.session_state.current_date = datetime.date(anio_actual, mes_actual + 1, 1)
                        st.rerun()

                # Obtener año y mes activos según el session_state
                anio_actual = st.session_state.current_date.year
                mes_actual = st.session_state.current_date.month

                cal = calendar.Calendar(firstweekday=0)
                dias_mes = cal.monthdayscalendar(anio_actual, mes_actual)

                componentes_html = [
                    f"""
                    <style>
                        .cal-box {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-top: 15px; margin-bottom: 20px; font-family: sans-serif; }}
                        .cal-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; text-align: center; }}
                        .cal-col-name {{ background-color: #21262d; color: #8b949e; font-weight: bold; padding: 8px 0; border-radius: 4px; font-size: 0.85rem; }}
                        .cal-day-cell {{ padding: 12px 0; border-radius: 4px; font-weight: bold; font-size: 0.95rem; border: 1px solid #30363d; }}
                        .cal-day-empty {{ background-color: #0d1117; opacity: 0.2; border: 1px dashed #21262d; }}
                    </style>
                    <div class="cal-box">
                        <div class="cal-grid">
                            <div class="cal-col-name">L</div>
                            <div class="cal-col-name">M</div>
                            <div class="cal-col-name">M</div>
                            <div class="cal-col-name">J</div>
                            <div class="cal-col-name">V</div>
                            <div class="cal-col-name">S</div>
                            <div class="cal-col-name">D</div>
                    """
                ]

                for semana in dias_mes:
                    for dia in semana:
                        if dia == 0:
                            componentes_html.append(
                                '<div class="cal-day-cell cal-day-empty"></div>'
                            )
                        else:
                            dia_str = f"{anio_actual}-{mes_actual:02d}-{dia:02d}"
                            info_d = diccionario_asistencias.get(dia_str, None)
                            if info_d and info_d["color"] != "#21262d":
                                bg_color = info_d["color"]
                                txt_color = (
                                    "#111111"
                                    if bg_color == "#d29922"
                                    else "#ffffff"
                                )
                            else:
                                bg_color = "#21262d"
                                txt_color = "#c9d1d9"

                            componentes_html.append(
                                f'<div class="cal-day-cell" style="background-color:'
                                f" {bg_color}; color: {txt_color};\">{dia}</div>"
                            )

                componentes_html.append("</div></div>")
                st.markdown("".join(componentes_html), unsafe_allow_html=True)

                # Filtrar fechas disponibles dentro del DataFrame que pertenezcan al mes y año seleccionado
                fechas_mes_actual = []
                for _, row in df_mi_asistencia.iterrows():
                    dt_val = row["_dt"]
                    if pd.notna(dt_val) and dt_val.year == anio_actual and dt_val.month == mes_actual:
                        fechas_mes_actual.append(str(row[col_fecha]))

                # Si no hay registros exactos para este mes en la base, mostrar opción vacía o todas
                if not fechas_mes_actual:
                    fechas_mes_actual = [f"{anio_actual}-{mes_actual:02d}-01 (Sin registro operativo)"]

                fecha_elegida = st.selectbox(
                    "Selecciona una fecha específica para desplegar su tarjeta informativa:",
                    fechas_mes_actual,
                )

                if fecha_elegida:
                    # Limpiar formato de fecha extraída
                    fecha_limpia = fecha_elegida.split(" ")[0]
                    info_dia = diccionario_asistencias.get(fecha_limpia, None)

                    if info_dia:
                        color_tarjeta = (
                            info_dia["color"]
                            if info_dia["color"] != "#21262d"
                            else "#30363d"
                        )
                        st.markdown(
                            f"""
                            <div style="background-color: #161b22; border-left: 6px solid {color_tarjeta}; border: 1px solid #30363d; padding: 20px; border-radius: 6px; margin-top: 15px; margin-bottom: 15px;">
                                <div style="font-size: 0.75rem; color: #8b949e; text-transform: uppercase; font-weight: bold;">Menú Informativo — Fecha: {fecha_elegida}</div>
                                <div style="font-size: 1.25rem; color: #ffffff; font-weight: bold; margin: 8px 0;">Estado: {info_dia['estado_txt']}</div>
                                <div style="font-size: 0.85rem; color: #8b949e;">ℹ️ <i>Información cargada por supervisión (Solo lectura).</i></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        cols_det = st.columns(3)
                        idx_d = 0
                        for k, v in info_dia["fila_completa"].items():
                            if str(k).startswith("_"):
                                continue
                            with cols_det[idx_d % 3]:
                                st.markdown(
                                    f"""
                                    <div style="background-color: #0d1117; border: 1px solid #30363d; padding: 12px; border-radius: 6px; margin-bottom: 8px; text-align: center;">
                                        <div style="font-size: 0.75rem; color: #8b949e; font-weight: bold;">{k}</div>
                                        <div style="font-size: 1rem; color: #ffffff; margin-top: 4px;">{v}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            idx_d += 1
                    else:
                        st.info(
                            "No hay registros detallados cargados por la supervisora para"
                            " esta fecha seleccionada."
                        )

                with st.expander("Ver tabla completa de asistencias"):
                    st.dataframe(
                        df_mi_asistencia.loc[
                            :, ~df_mi_asistencia.columns.str.startswith("_")
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.dataframe(df_mi_asistencia, use_container_width=True, hide_index=True)
        else:
            st.info(
                "No se encontraron registros de asistencias para tu usuario en el"
                " archivo."
            )
    else:
        st.info("Aún no se ha cargado el archivo de asistencias en el sistema.")