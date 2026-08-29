import os
import pandas as pd
import streamlit as st


def mostrar_wallboard_proyeccion(
    origen_retenciones, origen_nps, origen_ventas, objetivos
):
  """Wallboard de operaciones: Paneles sincronizados con totales reales,

  podios individuales filtrados y podio global consolidado.
  """

  # Cabecera de Alto Impacto para Pantalla Completa
  st.markdown(
      """
        <div style="text-align: center; padding: 5px 0 15px 0;">
            <h1 style='color: #58a6ff; font-size: 2.3rem; margin-bottom: 0;'>🧭 Proyecto Cardinal — Wallboard Operativo</h1>
            <p style='color: #8b949e; font-size: 1rem; margin-top: 5px;'>Monitoreo en tiempo real, cumplimiento de objetivos y podios de rendimiento</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # --- CARGA INTELIGENTE DE DATOS (SESIÓN O ARCHIVOS LOCALES) ---

  # 1. RETENCIONES (Contiene Retención y Beneficio)
  df_asesores_ret = pd.DataFrame()
  if not origen_retenciones and os.path.exists("datos_retenciones.xlsx"):
    origen_retenciones = "datos_retenciones.xlsx"

  if origen_retenciones:
    try:
      xls_ret = pd.ExcelFile(origen_retenciones)
      sheet_meta = (
          "Retes X asesor"
          if "Retes X asesor" in xls_ret.sheet_names
          else xls_ret.sheet_names[0]
      )
      df_asesores_ret = pd.read_excel(
          origen_retenciones, sheet_name=sheet_meta
      )
    except Exception:
      pass

  # 2. NPS
  df_asesores_nps = pd.DataFrame()
  if not origen_nps and os.path.exists("datos_nps.xlsx"):
    origen_nps = "datos_nps.xlsx"

  if origen_nps:
    try:
      xls_nps = pd.ExcelFile(origen_nps)
      sheet_nps = (
          xls_nps.sheet_names[0] if xls_nps.sheet_names else "Sheet1"
      )
      df_raw_nps = pd.read_excel(origen_nps, sheet_name=sheet_nps)

      if (
          "Unnamed" in str(df_raw_nps.columns[0])
          or "Cuenta" in str(df_raw_nps.iloc[1, 0]).title()
      ):
        for idx, row in df_raw_nps.iterrows():
          row_str = str(row.values).lower()
          if "etiquetas de fila" in row_str or "asesor" in row_str:
            df_raw_nps.columns = df_raw_nps.iloc[idx]
            df_asesores_nps = df_raw_nps.iloc[idx + 1 :].reset_index(
                drop=True
            )
            break
        if df_asesores_nps.empty:
          df_asesores_nps = df_raw_nps
      else:
        df_asesores_nps = df_raw_nps
    except Exception:
      df_asesores_nps = pd.DataFrame()

  # 3. VENTAS
  df_ventas = pd.DataFrame()
  if not origen_ventas and os.path.exists("datos_ventas.xlsx"):
    origen_ventas = "datos_ventas.xlsx"

  if origen_ventas:
    try:
      df_ventas = pd.read_excel(origen_ventas)
    except Exception:
      pass

  # --- EXTRACCIÓN DE METAS ---
  meta_rete = objetivos.get("rete_pct", 0.70)
  meta_bene = objetivos.get("beneficio_pct", 0.40)
  meta_nps_meta = objetivos.get("nps_pct", 0.65)
  meta_ventas = objetivos.get("ventas_grupal", 260)

  # --- MAPEO FLEXIBLE DE COLUMNAS Y DATOS ---

  col_asesor_ret, col_rete, col_bene = None, None, None
  if not df_asesores_ret.empty:
    cols_ret_map = {str(c).lower(): c for c in df_asesores_ret.columns}
    col_asesor_ret = next(
        (
            cols_ret_map[c]
            for c in cols_ret_map
            if "asesor" in c or "nombre" in c
        ),
        df_asesores_ret.columns[0],
    )
    col_rete = next(
        (
            cols_ret_map[c]
            for c in cols_ret_map
            if "rete" in c and ("%" in c or "cta" in c)
        ),
        None,
    )
    if not col_rete:
      col_rete = next(
          (cols_ret_map[c] for c in cols_ret_map if "rete" in c), None
      )
    col_bene = next(
        (cols_ret_map[c] for c in cols_ret_map if "beneficio" in c), None
    )

  col_asesor_v, col_ventas = None, None
  if not df_ventas.empty:
    cols_v_map = {str(c).lower(): c for c in df_ventas.columns}
    col_asesor_v = next(
        (cols_v_map[c] for c in cols_v_map if "asesor" in c or "nombre" in c),
        df_ventas.columns[0],
    )
    col_ventas = next(
        (
            cols_v_map[c]
            for c in cols_v_map
            if "venta" in c or "total" in c or "cantidad" in c
        ),
        df_ventas.columns[-1],
    )

  col_asesor_nps, col_promotor = None, None
  if not df_asesores_nps.empty:
    cols_nps_map = {str(c).lower(): c for c in df_asesores_nps.columns}
    col_asesor_nps = next(
        (
            cols_nps_map[c]
            for c in cols_nps_map
            if "etiquetas" in c
            or "asesor" in c
            or "nombre" in c
            or "cuenta" in c
        ),
        df_asesores_nps.columns[0],
    )
    col_promotor = next(
        (cols_nps_map[c] for c in cols_nps_map if "promotor" in c), None
    )

  # --- FUNCIÓN FILTRADORA DE TOTALES (PARA PODIOS) ---
  def filtrar_asesores_validos(df, col_nom):
    if df.empty or not col_nom or col_nom not in df.columns:
      return pd.DataFrame()

    df_f = df.dropna(subset=[col_nom]).copy()
    palabras_prohibidas = [
        "total",
        "suma",
        "promedio",
        "general",
        "nan",
        "none",
        "subtotal",
        "blank",
    ]

    def es_valido(val):
      v_str = str(val).strip().lower()
      if not v_str or v_str == "nan" or v_str == "none":
        return False
      for palabra in palabras_prohibidas:
        if palabra in v_str:
          return False
      return True

    df_f = df_f[df_f[col_nom].apply(es_valido)]
    return df_f

  # --- CÁLCULO DE TOTALES GLOBALES (BUSCANDO LA FILA DE TOTALES O USANDO VALORES LIMPIOS) ---
  total_rete_real = 0.0
  total_bene_real = 0.0
  total_ventas_real = 0

  if not df_asesores_ret.empty:
    # Buscar si existe una fila explícita de "Total" o "Total general" en la planilla
    fila_total = df_asesores_ret[
        df_asesores_ret[col_asesor_ret]
        .astype(str)
        .str.lower()
        .str.contains("total|general", na=False)
    ]
    if not fila_total.empty and col_rete and col_rete in df_asesores_ret.columns:
      val_t = pd.to_numeric(fila_total[col_rete].values[0], errors="coerce")
      if not pd.isna(val_t):
        total_rete_real = val_t

    if not fila_total.empty and col_bene and col_bene in df_asesores_ret.columns:
      val_b = pd.to_numeric(fila_total[col_bene].values[0], errors="coerce")
      if not pd.isna(val_b):
        total_bene_real = val_b

    # Si no hay fila de totales explícita, calcular sobre asesores válidos filtrados
    if total_rete_real == 0.0 and col_rete:
      df_val_r = filtrar_asesores_validos(df_asesores_ret, col_asesor_ret)
      if not df_val_r.empty:
        total_rete_real = (
            pd.to_numeric(df_val_r[col_rete], errors="coerce").mean() or 0.0
        )

    if total_bene_real == 0.0 and col_bene:
      df_val_b = filtrar_asesores_validos(df_asesores_ret, col_asesor_ret)
      if not df_val_b.empty:
        total_bene_real = (
            pd.to_numeric(df_val_b[col_bene], errors="coerce").mean() or 0.0
        )

  if not df_ventas.empty and col_ventas:
    fila_total_v = df_ventas[
        df_ventas[col_asesor_v]
        .astype(str)
        .str.lower()
        .str.contains("total|general", na=False)
    ]
    if not fila_total_v.empty:
      val_v = pd.to_numeric(fila_total_v[col_ventas].values[0], errors="coerce")
      if not pd.isna(val_v):
        total_ventas_real = int(val_v)
    if total_ventas_real == 0:
      df_val_v = filtrar_asesores_validos(df_ventas, col_asesor_v)
      if not df_val_v.empty:
        total_ventas_real = int(
            pd.to_numeric(df_val_v[col_ventas], errors="coerce").sum() or 0
        )

  # --- PANELES SUPERIORES: TOTALES VS OBJETIVOS ---
  col1, col2, col3, col4 = st.columns(4)

  def get_badge(actual, meta, is_percentage=True):
    if is_percentage:
      ok = actual >= meta
      color = "#3fb950" if ok else "#f85149"
      texto = "¡Cumplido!" if ok else "Abajo"
    else:
      ok = actual >= meta
      color = "#3fb950" if ok else "#f59e0b"
      texto = "¡Cumplido!" if ok else "En Progreso"
    return f'<span style="color: {color}; font-size: 0.75rem; font-weight: bold;">{texto}</span>'

  with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">% RETE CTA (Global)</div>
            <div class="metric-value">{total_rete_real*100:.1f}%</div>
            <div style="margin-top: 5px;">{get_badge(total_rete_real, meta_rete)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">BENEFICIO (Global)</div>
            <div class="metric-value">{total_bene_real*100:.1f}%</div>
            <div style="margin-top: 5px;">{get_badge(total_bene_real, meta_bene)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">NPS Positivo</div>
            <div class="metric-value">{meta_nps_meta*100:.1f}%</div>
            <div style="margin-top: 5px;"><span style="color: #58a6ff; font-size: 0.75rem; font-weight: bold;">Monitoreo</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Ventas Grupales</div>
            <div class="metric-value">{total_ventas_real}</div>
            <div style="margin-top: 5px;">{get_badge(total_ventas_real, meta_ventas, is_percentage=False)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- COMPONENTE AUXILIAR PARA RENDERIZAR TARJETAS DE PODIO ---
  def render_podio_card(
      titulo,
      color_titulo,
      df_fuente,
      col_nom,
      col_val,
      es_porcentaje=True,
      unidad="",
  ):
    st.markdown(
        f"<h5 style='text-align: center; color: {color_titulo}; margin-bottom:"
        f" 10px;'>{titulo}</h5>",
        unsafe_allow_html=True,
    )

    df_limpio = filtrar_asesores_validos(df_fuente, col_nom)

    if not df_limpio.empty and col_val and col_val in df_limpio.columns:
      df_temp = df_limpio[[col_nom, col_val]].copy()
      df_temp[col_val] = pd.to_numeric(df_temp[col_val], errors="coerce")
      df_temp = df_temp.dropna().sort_values(by=col_val, ascending=False).head(3)

      medals = ["🥇", "🥈", "🥉"]
      for idx, row in enumerate(df_temp.itertuples(), start=0):
        medalla = medals[idx] if idx < 3 else f"#{idx+1}"
        nombre = str(row[1])
        val_bruto = float(row[2])
        val_mostrar = (
            f"{val_bruto*100:.1f}%"
            if es_porcentaje and val_bruto <= 1.0
            else f"{val_bruto:.1f}{unidad}"
            if es_porcentaje
            else f"{int(val_bruto)} {unidad}"
        )

        st.markdown(
            f"""
            <div style="background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.95rem; font-weight: bold; color: #ffffff;">{medalla} {nombre}</span>
                <span style="font-size: 0.95rem; font-weight: bold; color: {color_titulo};">{val_mostrar}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
      st.markdown(
          """
            <div style="background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 6px; text-align: center; color: #8b949e; font-size: 0.85rem;">
                Sin datos suficientes
            </div>
            """,
          unsafe_allow_html=True,
      )

  # --- 4 PODIOS INDIVIDUALES ---
  st.markdown(
      "<h3 style='color: #c9d1d9; text-align: center; margin-bottom: 15px;'>🏆"
      " Podios por Métrica Operativa</h3>",
      unsafe_allow_html=True,
  )

  p1, p2, p3, p4 = st.columns(4)

  with p1:
    render_podio_card(
        "🥇 Retención CTA",
        "#3fb950",
        df_asesores_ret,
        col_asesor_ret,
        col_rete,
        es_porcentaje=True,
    )

  with p2:
    render_podio_card(
        "🥈 % Beneficio",
        "#58a6ff",
        df_asesores_ret,
        col_asesor_ret,
        col_bene,
        es_porcentaje=True,
    )

  with p3:
    col_nps_val_clean = (
        col_promotor
        if (not df_asesores_nps.empty and col_promotor)
        else (df_asesores_nps.columns[-1] if not df_asesores_nps.empty else None)
    )
    render_podio_card(
        "⭐ NPS Destacados",
        "#f0883e",
        df_asesores_nps,
        col_asesor_nps,
        col_nps_val_clean,
        es_porcentaje=False,
        unidad=" un.",
    )

  with p4:
    render_podio_card(
        "🚀 Ventas Grupales",
        "#a371f7",
        df_ventas,
        col_asesor_v,
        col_ventas,
        es_porcentaje=False,
        unidad=" un.",
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- PODIO GLOBAL CONSOLIDADO ---
  st.markdown(
      "<h3 style='color: #c9d1d9; text-align: center; margin-bottom: 15px;'>🌟"
      " Podio Global Consolidado del Equipo</h3>",
      unsafe_allow_html=True,
  )

  try:
    df_global_list = []

    if not df_asesores_ret.empty and col_asesor_ret and col_rete:
      df_r_clean = filtrar_asesores_validos(df_asesores_ret, col_asesor_ret)
      if not df_r_clean.empty:
        df_r_temp = df_r_clean[[col_asesor_ret, col_rete]].copy()
        df_r_temp.columns = ["Asesor", "Score_Ret"]
        df_r_temp["Score_Ret"] = (
            pd.to_numeric(df_r_temp["Score_Ret"], errors="coerce")
            .fillna(0)
        )
        if df_r_temp["Score_Ret"].max() <= 1.0:
          df_r_temp["Score_Ret"] = df_r_temp["Score_Ret"] * 100
        df_global_list.append(df_r_temp)

    if not df_ventas.empty and col_asesor_v and col_ventas:
      df_v_clean = filtrar_asesores_validos(df_ventas, col_asesor_v)
      if not df_v_clean.empty:
        df_v_temp = df_v_clean[[col_asesor_v, col_ventas]].copy()
        df_v_temp.columns = ["Asesor", "Score_Ventas"]
        df_v_temp["Score_Ventas"] = (
            pd.to_numeric(df_v_temp["Score_Ventas"], errors="coerce")
            .fillna(0)
        )
        max_v = df_v_temp["Score_Ventas"].max()
        if max_v > 0:
          df_v_temp["Score_Ventas"] = (
              df_v_temp["Score_Ventas"] / max_v
          ) * 100
        df_global_list.append(df_v_temp)

    if len(df_global_list) > 0:
      from functools import reduce

      df_merged = reduce(
          lambda left, right: pd.merge(left, right, on="Asesor", how="outer"),
          df_global_list,
      ).fillna(0)
      score_cols = [c for c in df_merged.columns if c != "Asesor"]
      df_merged["Score_Global"] = df_merged[score_cols].mean(axis=1)
      df_global_top = (
          df_merged.sort_values(by="Score_Global", ascending=False).head(3)
      )

      col_g1, col_g2, col_g3 = st.columns(3)
      global_medals = ["👑 1° PUESTO", "🥈 2° PUESTO", "🥉 3° PUESTO"]
      global_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]

      for idx, row in enumerate(df_global_top.itertuples(), start=0):
        col_actual = [col_g1, col_g2, col_g3][idx]
        nombre_asesor = str(row[1])
        score_val = float(row[-1])
        with col_actual:
          st.markdown(
              f"""
              <div style="background: linear-gradient(135deg, #161b22 0%, #21262d 100%); border: 2px solid {global_colors[idx]}; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                  <div style="font-size: 0.85rem; font-weight: bold; color: {global_colors[idx]}; margin-bottom: 5px;">{global_medals[idx]}</div>
                  <div style="font-size: 1.2rem; font-weight: bold; color: #ffffff; margin-bottom: 8px;">{nombre_asesor}</div>
                  <div style="font-size: 0.9rem; color: #8b949e;">Índice General</div>
                  <div style="font-size: 1.4rem; font-weight: bold; color: #58a6ff;">{score_val:.1f} pts</div>
              </div>
              """,
              unsafe_allow_html=True,
          )
    else:
      st.info(
          "Cargue las planillas operativas válidas para habilitar el cálculo"
          " del podio global."
      )
  except Exception:
    st.info("No se pudo calcular el podio global con los datos actuales.")