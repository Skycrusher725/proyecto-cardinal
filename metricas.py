import pandas as pd


def calcular_semaforo(valor_actual, valor_objetivo):
  """Retorna (color_hex, etiqueta_estado, clase_css) basado en el cumplimiento."""
  if valor_objetivo == 0:
    return "#8b949e", "Sin Meta", "sem-gris"

  cumplimiento = valor_actual / valor_objetivo

  if cumplimiento >= 1.0:
    return "#3fb950", "¡Cumplido!", "sem-verde"
  elif cumplimiento >= 0.85:
    return "#f59e0b", "Cerca", "sem-amarillo"
  else:
    return "#f85149", "Alerta", "sem-rojo"


def calcular_porcentaje_nps_positivo(df):
  """Calcula el porcentaje de evaluaciones positivas en el DataFrame de NPS de forma segura."""
  if df is None or df.empty:
    return 0.0

  try:
    df = df.dropna(how="all")
    if df.empty:
      return 0.0

    # Buscar una columna candidata de forma segura
    palabras_clave = [
        "nps",
        "satisf",
        "puntaje",
        "score",
        "evaluacion",
        "tipo",
        "clasif",
        "resultado",
        "valor",
    ]
    cols_nps = []
    for c in df.columns:
      c_str = str(c).lower()
      if any(k in c_str for k in palabras_clave):
        cols_nps.append(str(c))

    col_objetivo = cols_nps[0] if cols_nps else df.columns[-1]

    total_registros = len(df)
    if total_registros == 0:
      return 0.0

    positivos = 0
    serie_limpia = df[col_objetivo].fillna("").astype(str).str.lower().str.strip()

    palabras_positivas = [
        "promotor",
        "positivo",
        "satis",
        "excelente",
        "bueno",
        "si",
        "verde",
        "cumplido",
    ]

    for val in serie_limpia:
      encontrado = False
      for p in palabras_positivas:
        if p in val:
          encontrado = True
          break

      if encontrado:
        positivos += 1
      else:
        try:
          num = float(val.replace(",", ".").replace("%", ""))
          if num >= 8 or (num >= 0.8 and num <= 1.0):
            positivos += 1
        except Exception:
          pass

    if positivos == 0:
      try:
        valores_num = pd.to_numeric(
            df[col_objetivo]
            .astype(str)
            .str.replace(",", ".")
            .str.replace("%", ""),
            errors="coerce",
        )
        positivos = (valores_num >= 8).sum()
      except Exception:
        pass

    return positivos / total_registros
  except Exception:
    return 0.0