import os
import base64
import pandas as pd
import streamlit as st


def mostrar_panel_admin(
    origen_retenciones, origen_nps, origen_ventas, objetivos, rol
):
  """Panel exclusivo para Administradores, Masters y Supervisores con NPS global agregado."""
  
  # Obtener nombre/clave de usuario para la foto
  user_key = st.session_state.get("user", "Admin")
  nombre_mostrar = st.session_state.get("nombre_mostrar", "Administrador / Supervisor")
  
  # Buscar foto de perfil en carpeta 'fotos/'
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

  # Carga de datos con persistencia (lee el archivo subido o el guardado en disco)
  df_ret = (
      pd.read_excel(origen_retenciones)
      if origen_retenciones
      else (
          pd.read_excel("datos_retenciones.xlsx")
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

  # Cálculo de globales
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
      tot_rete = pd.to_numeric(df_ret[col_r], errors="coerce").mean() or 0.0
    if col_b:
      tot_bene = pd.to_numeric(df_ret[col_b], errors="coerce").mean() or 0.0

  if not df_ventas.empty:
    col_v = df_ventas.columns[-1]
    tot_ventas = int(pd.to_numeric(df_ventas[col_v], errors="coerce").sum() or 0)

  # Tarjetas superiores administradores
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">% RETE CTA (Global)</div><div class="metric-value">{tot_rete*100:.1f}%</div></div>',
        unsafe_allow_html=True,
    )
  with c2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">BENEFICIO (Global)</div><div class="metric-value">{tot_bene*100:.1f}%</div></div>',
        unsafe_allow_html=True,
    )
  with c3:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">NPS Positivo</div><div class="metric-value">80.0%</div></div>',
        unsafe_allow_html=True,
    )
  with c4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Ventas Grupales</div><div class="metric-value">{tot_ventas}</div></div>',
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.subheader("📋 Detalle Operativo General")

  # Primera fila de tablas: Retenciones (mostrando asesores/grupos) y Ventas
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

  # Segunda fila: Detalle de NPS agregado abajo de todo tal como se solicitó
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
  """Panel exclusivo para Asesores con persistencia y lectura precisa."""

  # Buscar foto de perfil en carpeta 'fotos/' con el nombre de usuario
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

  # Carga de planillas persistidas en disco para el asesor
  df_ret = (
      pd.read_excel(origen_retenciones)
      if origen_retenciones
      else (
          pd.read_excel("datos_retenciones.xlsx")
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

  # --- FUNCIÓN DE FILTRADO DIRECTO Y ROBUSTO ---
  def filtrar_dataframe(df):
    if df.empty:
      return df
    col_nombre = df.columns[0]
    texto_a_buscar = asesor_objetivo if asesor_objetivo else nombre_mostrar

    # Buscar coincidencia flexible ignorando mayúsculas/minúsculas y espacios extras
    condicion = (
        df[col_nombre]
        .astype(str)
        .str.lower()
        .str.strip()
        .str.contains(str(texto_a_buscar).lower().strip(), na=False)
    )
    resultado = df[condicion]
    return resultado

  # Filtrar datos de retenciones
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
          (c for c in df_ret.columns if "beneficio" in str(c).lower()), None
      )

      if col_r:
        mi_rete_val = (
            pd.to_numeric(filtro_asesor[col_r].values[0], errors="coerce")
            or 0.0
        )
      if col_b:
        mi_bene_val = (
            pd.to_numeric(filtro_asesor[col_b].values[0], errors="coerce")
            or 0.0
        )

  # Filtrar ventas del asesor
  mi_venta_val = 0
  df_mi_ventas = pd.DataFrame()
  if not df_ventas.empty:
    filtro_v = filtrar_dataframe(df_ventas)
    col_vv = df_ventas.columns[-1]
    if not filtro_v.empty:
      df_mi_ventas = filtro_v
      mi_venta_val = (
          int(
              pd.to_numeric(filtro_v[col_vv].values[0], errors="coerce") or 0
          )
      )

  # Filtrar NPS del asesor
  df_mi_nps = pd.DataFrame()
  if not df_nps.empty:
    filtro_nps = filtrar_dataframe(df_nps)
    if not filtro_nps.empty:
      df_mi_nps = filtro_nps

  # --- TARJETAS INDIVIDUALES ---
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

  # --- CUADROS E INDICADORES INDIVIDUALES ---
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