import os
import calendar
import pandas as pd
import streamlit as st
from datetime import datetime


def mostrar_gestion_asistencias():
  """Módulo exclusivo para Supervisores/Administradores para control de asistencias."""

  st.markdown(
      """
        <div style="text-align: center; padding: 5px 0 15px 0;">
            <h1 style='color: #58a6ff; font-size: 2.2rem; margin-bottom: 0;'>📅 Gestión de Asistencias y Horas</h1>
            <p style='color: #8b949e; font-size: 0.95rem; margin-top: 5px;'>Control operativo diario por asesor y reporte para administración</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # --- ESTILOS CSS DINÁMICOS PARA COLOREAR LOS BOTONES DE FECHA ---
  st.markdown(
      """
        <style>
        /* Estilo base para los expansores / botones de días */
        div[data-testid="stExpander"] {
            border: 1px solid #30363d;
            border-radius: 8px;
            background-color: #161b22;
            margin-bottom: 5px;
        }
        
        /* Clases personalizadas inyectadas por estado */
        .card-presente {
            background-color: rgba(63, 185, 80, 0.25) !important;
            border: 1px solid #3fb950 !important;
        }
        .card-ausente {
            background-color: rgba(248, 81, 73, 0.25) !important;
            border: 1px solid #f85149 !important;
        }
        .card-retiro {
            background-color: rgba(227, 179, 65, 0.25) !important;
            border: 1px solid #e3b341 !important;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  # Archivo de persistencia para asistencias
  archivo_asistencias = "datos_asistencias.xlsx"

  # Cargar base de datos existente o crear una vacía con la estructura correcta
  if os.path.exists(archivo_asistencias):
    df_asist = pd.read_excel(archivo_asistencias)
  else:
    df_asist = pd.DataFrame(
        columns=[
            "Asesor",
            "Año",
            "Mes",
            "Fecha",
            "Estado",
            "Motivo_Retiro",
            "Ultima_Modificacion",
        ]
    )

  # Intentar obtener la lista de asesores desde las planillas ya cargadas
  asesores_lista = []
  for arch in ["datos_retenciones.xlsx", "datos_ventas.xlsx"]:
    if os.path.exists(arch):
      try:
        temp_df = pd.read_excel(arch)
        if not temp_df.empty:
          col_nombres = temp_df.columns[0]
          nombres = temp_df[col_nombres].dropna().astype(str).tolist()
          asesores_lista.extend(nombres)
      except Exception:
        pass

  asesores_lista = sorted(list(set([a.strip() for a in asesores_lista if a.strip()])))
  if not asesores_lista:
    asesores_lista = [
        "AGUIRRE ERIKA",
        "Ejemplo Asesor 1",
        "Ejemplo Asesor 2",
    ]

  # --- FILTROS SUPERIORES: ASESOR, AÑO Y MES ---
  col_f1, col_f2, col_f3 = st.columns(3)

  with col_f1:
    asesor_seleccionado = st.selectbox("Seleccionar Asesor", asesores_lista)

  with col_f2:
    current_year = datetime.now().year
    anos_disponibles = list(range(current_year - 1, current_year + 3))
    anio_seleccionado = st.selectbox(
        "Año", anos_disponibles, index=anos_disponibles.index(current_year)
    )

  with col_f3:
    meses_dict = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    mes_nombre = st.selectbox(
        "Mes",
        list(meses_dict.values()),
        index=datetime.now().month - 1,
    )
    mes_seleccionado = [
        k for k, v in meses_dict.items() if v == mes_nombre
    ][0]

  st.markdown("---")

  # --- CONSTRUCCIÓN DEL CALENDARIO ---
  st.subheader(
      f"🗓️ Calendario de Asistencia: {asesor_seleccionado} ({mes_nombre} {anio_seleccionado})"
  )
  st.markdown(
      "<p style='color: #8b949e; font-size: 0.9rem;'>Haga clic en una fecha"
      " para desplegar las opciones de asistencia.</p>",
      unsafe_allow_html=True,
  )

  cal = calendar.Calendar(firstweekday=0)
  dias_mes = cal.monthdayscalendar(anio_seleccionado, mes_seleccionado)

  dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
  cols_semana = st.columns(7)
  for i, d_sem in enumerate(dias_semana):
    cols_semana[i].markdown(
        f"<div style='text-align: center; font-weight: bold; color: #58a6ff;'>{d_sem}</div>",
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  df_asesor_mes = df_asist[
      (df_asist["Asesor"] == asesor_seleccionado)
      & (df_asist["Año"] == anio_seleccionado)
      & (df_asist["Mes"] == mes_seleccionado)
  ]

  estado_dict = {}
  motivo_dict = {}
  if not df_asesor_mes.empty:
    for _, row in df_asesor_mes.iterrows():
      estado_dict[str(row["Fecha"])] = row["Estado"]
      motivo_dict[str(row["Fecha"])] = (
          row["Motivo_Retiro"] if pd.notna(row["Motivo_Retiro"]) else ""
      )

  for semana in dias_mes:
    cols_dias = st.columns(7)
    for i, dia in enumerate(semana):
      if dia == 0:
        cols_dias[i].markdown("")
        continue

      fecha_str = f"{anio_seleccionado}-{mes_seleccionado:02d}-{dia:02d}"
      estado_actual = estado_dict.get(fecha_str, "Sin registrar")

      # Definir colores y etiquetas de estilo según el estado
      if estado_actual == "Presente":
        bg_color = "rgba(63, 185, 80, 0.25)"
        border_color = "#3fb950"
        text_color = "#3fb950"
        badge_class = "card-presente"
      elif estado_actual == "Ausente":
        bg_color = "rgba(248, 81, 73, 0.25)"
        border_color = "#f85149"
        text_color = "#f85149"
        badge_class = "card-ausente"
      elif estado_actual == "Se retiró":
        bg_color = "rgba(227, 179, 65, 0.25)"
        border_color = "#e3b341"
        text_color = "#e3b341"
        badge_class = "card-retiro"
      else:
        bg_color = "#161b22"
        border_color = "#30363d"
        text_color = "#8b949e"
        badge_class = ""

      with cols_dias[i]:
        # Contenedor visual coloreado mediante HTML envolvente para el botón/expansor
        st.markdown(
            f"""
                <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 2px; text-align: center; margin-bottom: -15px;">
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"Día {dia} ({estado_actual[0]})"):
          st.markdown(
              f"""
                        <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px; text-align: center; margin-bottom: 8px;">
                            <span style="color: {text_color}; font-weight: bold; font-size: 0.85rem;">{estado_actual}</span>
                        </div>
                    """,
              unsafe_allow_html=True,
          )

          nuevo_estado = st.selectbox(
              "Estado",
              ["Sin registrar", "Presente", "Ausente", "Se retiró"],
              index=(
                  ["Sin registrar", "Presente", "Ausente", "Se retiró"].index(
                      estado_actual
                  )
                  if estado_actual
                  in ["Sin registrar", "Presente", "Ausente", "Se retiró"]
                  else 0
              ),
              key=f"est_{asesor_seleccionado}_{fecha_str}",
          )

          motivo_actual = motivo_dict.get(fecha_str, "")
          motivo_retiro = ""
          if nuevo_estado == "Se retiró":
            motivo_retiro = st.text_input(
                "Motivo de retiro",
                value=motivo_actual,
                key=f"mot_{asesor_seleccionado}_{fecha_str}",
            )

          if st.button(
              "Guardar", key=f"btn_{asesor_seleccionado}_{fecha_str}"
          ):
            timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            global_idx = df_asist[
                (df_asist["Asesor"] == asesor_seleccionado)
                & (df_asist["Fecha"] == fecha_str)
            ].index

            if not global_idx.empty:
              df_asist = df_asist.drop(global_idx)

            if nuevo_estado != "Sin registrar":
              nuevo_registro = pd.DataFrame([
                  {
                      "Asesor": asesor_seleccionado,
                      "Año": anio_seleccionado,
                      "Mes": mes_seleccionado,
                      "Fecha": fecha_str,
                      "Estado": nuevo_estado,
                      "Motivo_Retiro": motivo_retiro
                      if nuevo_estado == "Se retiró"
                      else "",
                      "Ultima_Modificacion": timestamp_actual,
                  }
              ])
              df_asist = pd.concat([df_asist, nuevo_registro], ignore_index=True)

            df_asist.to_excel(archivo_asistencias, index=False)
            st.success(f"Guardado para el día {dia}")
            st.rerun()

  st.markdown("---")

  # --- SECCIÓN DE REPORTES Y DESCARGA PARA ADMINISTRACIÓN ---
  st.subheader("📊 Reporte Global de Asistencias y Horas")
  st.markdown(
      "Descargue la planilla completa consolidada para el control de"
      " administración."
  )

  if not df_asist.empty:
    st.dataframe(df_asist, use_container_width=True)

    @st.cache_data
    def convertir_df_a_excel(df):
      from io import BytesIO

      output = BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Asistencias")
      processed_data = output.getvalue()
      return processed_data

    excel_data = convertir_df_a_excel(df_asist)

    st.download_button(
        label="📥 Descargar Planilla de Asistencias (Excel)",
        data=excel_data,
        file_name="Reporte_Asistencias_Administracion.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
  else:
    st.info(
        "Aún no hay registros de asistencia guardados en el sistema para"
        " exportar."
    )