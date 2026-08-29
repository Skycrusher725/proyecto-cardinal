import pandas as pd


def obtener_top_podio(df, col_criterio, n=3, ascendente=False):
  """Obtiene el Top N de asesores según el criterio seleccionado en el DataFrame."""
  if df is None or df.empty or col_criterio not in df.columns:
    return pd.DataFrame()

  df_clean = df.copy()
  df_clean[col_criterio] = pd.to_numeric(
      df_clean[col_criterio]
      .astype(str)
      .str.replace("%", "")
      .str.replace(",", ".")
      .str.strip(),
      errors="coerce",
  )
  df_clean = df_clean.dropna(subset=[col_criterio])
  df_sorted = df_clean.sort_values(by=col_criterio, ascending=ascendente)
  return df_sorted.head(n)


def calcular_podio_general(df_asesores_ret, n=3):
  """Calcula y estructura los podios principales (ej.

  % RETE CTA y Beneficio) para visualización en paneles y wallboards.
  """
  if df_asesores_ret is None or df_asesores_ret.empty:
    return pd.DataFrame(), pd.DataFrame()

  top_retes = obtener_top_podio(df_asesores_ret, "% RETE CTA", n=n)
  top_benef = obtener_top_podio(df_asesores_ret, "Beneficio", n=n)

  return top_retes, top_benef