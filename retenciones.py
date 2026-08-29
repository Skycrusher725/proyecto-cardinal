import os
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_EXCEL = "datos_retenciones.xlsx"

HOJA_GRUPO = "Retes X grupo"
HOJA_ASESOR = "Retes X asesor"
HOJA_RESUMEN = "Resumen Retes"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_nombre(nombre):
    """
    Limpia espacios innecesarios de los nombres de asesores.
    """

    if pd.isna(nombre):
        return ""

    return str(nombre).strip()


def es_total(nombre):
    """
    Determina si una fila corresponde a un total general.
    """

    if pd.isna(nombre):
        return False

    texto = str(nombre).strip().lower()

    return (
        texto == "total general"
        or
        texto == "total"
        or
        texto == "subtotal"
        or
        texto == "general"
    )


def es_fila_total(valor):
    """
    Versión flexible utilizada por el panel.
    """

    if pd.isna(valor):
        return False

    texto = str(valor).strip().lower()

    palabras = [
        "total",
        "subtotal",
        "general",
        "suma"
    ]

    return any(
        palabra in texto
        for palabra in palabras
    )


# ============================================================
# CONVERSIÓN DE NÚMEROS Y PORCENTAJES
# ============================================================

def convertir_porcentaje(valor):
    """
    Convierte un valor de porcentaje a decimal.

    Ejemplos:

        0.722334 -> 0.722334
        72.23    -> 0.7223
        "72.23%" -> 0.7223
        "72,23%" -> 0.7223
    """

    if pd.isna(valor):
        return 0.0

    if isinstance(valor, str):

        texto = valor.strip()

        if not texto:
            return 0.0

        tiene_porcentaje = "%" in texto

        texto = texto.replace("%", "").strip()

        if "," in texto and "." in texto:
            texto = texto.replace(".", "")
            texto = texto.replace(",", ".")

        elif "," in texto:
            texto = texto.replace(",", ".")

        try:
            numero = float(texto)

        except (ValueError, TypeError):
            return 0.0

        if tiene_porcentaje or numero > 1:
            numero = numero / 100

        return numero

    try:
        numero = float(valor)

    except (ValueError, TypeError):
        return 0.0

    if numero > 1:
        numero = numero / 100

    return numero


def convertir_numero(valor):
    """
    Convierte valores generales provenientes de Excel
    a número.

    Soporta:

        72%
        72,5%
        0,72
        0.72
        1.234,56
    """

    if pd.isna(valor):
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if not texto:
        return None

    tiene_porcentaje = "%" in texto

    texto = texto.replace("%", "").strip()

    if "," in texto and "." in texto:

        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    elif "," in texto:

        texto = texto.replace(",", ".")

    try:

        numero = float(texto)

        if tiene_porcentaje:
            numero = numero / 100

        return numero

    except (ValueError, TypeError):

        return None


def normalizar_porcentaje(valor):
    """
    Normaliza un porcentaje para trabajar internamente
    entre 0 y 1.

    Ejemplos:

        72      -> 0.72
        72%     -> 0.72
        0.72    -> 0.72
    """

    numero = convertir_numero(valor)

    if numero is None:
        return None

    if numero > 1:
        numero = numero / 100

    return numero


def formatear_porcentaje(valor):
    """
    Devuelve un porcentaje listo para mostrar.
    """

    numero = normalizar_porcentaje(valor)

    if numero is None:
        return "N/A"

    return f"{numero * 100:.1f}%"


# ============================================================
# BÚSQUEDA FLEXIBLE DE COLUMNAS
# ============================================================

def buscar_columna_por_nombres(df, nombres):
    """
    Busca una columna de forma flexible.
    """

    if df is None or df.empty:
        return None

    for columna in df.columns:

        nombre_columna = (
            str(columna)
            .strip()
            .lower()
        )

        for nombre in nombres:

            if nombre.lower() in nombre_columna:
                return columna

    return None


def buscar_columna_asesor(df):
    """
    Detecta la columna donde aparece el nombre del asesor.
    """

    if df is None or df.empty:
        return None

    posibles = [
        "asesor",
        "nombre",
        "agente",
        "etiqueta",
        "empleado",
        "usuario",
        "fila"
    ]

    return buscar_columna_por_nombres(
        df,
        posibles
    )


def buscar_columna_rete_cta(df):
    """
    Busca específicamente el porcentaje de RETE CTA.
    """

    if df is None or df.empty:
        return None

    candidatos_exactos = [
        "% rete cta",
        "%rete cta",
        "rete cta",
        "rete_cta",
        "retecta",
        "% rete",
        "rete"
    ]

    for columna in df.columns:

        nombre = (
            str(columna)
            .strip()
            .lower()
        )

        if nombre in candidatos_exactos:
            return columna

    # Segunda búsqueda flexible

    for columna in df.columns:

        nombre = (
            str(columna)
            .strip()
            .lower()
        )

        if (
            "rete" in nombre
            and "cta" in nombre
        ):
            return columna

    # Último recurso

    for columna in df.columns:

        nombre = (
            str(columna)
            .strip()
            .lower()
        )

        if "rete" in nombre:
            return columna

    return None


def buscar_columna_beneficio(df):
    """
    Busca específicamente el porcentaje de BENEFICIO.
    """

    if df is None or df.empty:
        return None

    candidatos_exactos = [
        "% beneficio",
        "%beneficio",
        "beneficio",
        "benefic",
        "% benefic",
        "% benef"
    ]

    for columna in df.columns:

        nombre = (
            str(columna)
            .strip()
            .lower()
        )

        if nombre in candidatos_exactos:
            return columna

    for columna in df.columns:

        nombre = (
            str(columna)
            .strip()
            .lower()
        )

        if "benef" in nombre:
            return columna

    return None


# ============================================================
# LECTURA GENÉRICA DE HOJAS EXCEL
# ============================================================

def cargar_hoja_excel(filepath, sheet_name):
    """
    Carga una hoja de Excel y limpia los nombres de columnas.

    Esta función mantiene compatibilidad con app.py.
    """

    if not os.path.exists(filepath):
        return None

    try:

        df = pd.read_excel(
            filepath,
            sheet_name=sheet_name
        )

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        return df

    except Exception as e:

        print(
            f"Error leyendo hoja {sheet_name}: {e}"
        )

        return None


# ============================================================
# LECTURA COMPLETA DEL EXCEL DE RETENCIONES
# ============================================================

def leer_retenciones():
    """
    Lee las tres hojas principales del archivo de retenciones.

    Devuelve:

        grupo
        asesor
        resumen
        total
    """

    archivo = Path(ARCHIVO_EXCEL)

    if not archivo.exists():

        raise FileNotFoundError(
            f"No se encontró el archivo "
            f"'{ARCHIVO_EXCEL}' "
            f"en la carpeta del proyecto."
        )

    # ========================================================
    # HOJA: RETES X GRUPO
    # ========================================================

    df_grupo = pd.read_excel(
        archivo,
        sheet_name=HOJA_GRUPO
    )

    df_grupo.columns = [
        str(col).strip()
        for col in df_grupo.columns
    ]

    if "GRUPO" not in df_grupo.columns:

        raise ValueError(
            f"La hoja '{HOJA_GRUPO}' "
            f"no contiene la columna 'GRUPO'."
        )

    if "% RETE CTA" not in df_grupo.columns:

        raise ValueError(
            f"La hoja '{HOJA_GRUPO}' "
            f"no contiene la columna '% RETE CTA'."
        )

    if "Beneficio" not in df_grupo.columns:

        raise ValueError(
            f"La hoja '{HOJA_GRUPO}' "
            f"no contiene la columna 'Beneficio'."
        )

    df_grupo["GRUPO"] = (
        df_grupo["GRUPO"]
        .apply(limpiar_nombre)
    )

    df_grupo["% RETE CTA"] = (
        df_grupo["% RETE CTA"]
        .apply(convertir_porcentaje)
    )

    df_grupo["Beneficio"] = (
        df_grupo["Beneficio"]
        .apply(convertir_porcentaje)
    )


    # ========================================================
    # HOJA: RETES X ASESOR
    # ========================================================

    df_asesor = pd.read_excel(
        archivo,
        sheet_name=HOJA_ASESOR
    )

    df_asesor.columns = [
        str(col).strip()
        for col in df_asesor.columns
    ]

    if "Asesor" not in df_asesor.columns:

        raise ValueError(
            f"La hoja '{HOJA_ASESOR}' "
            f"no contiene la columna 'Asesor'."
        )

    if "% RETE CTA" not in df_asesor.columns:

        raise ValueError(
            f"La hoja '{HOJA_ASESOR}' "
            f"no contiene la columna '% RETE CTA'."
        )

    if "Beneficio" not in df_asesor.columns:

        raise ValueError(
            f"La hoja '{HOJA_ASESOR}' "
            f"no contiene la columna 'Beneficio'."
        )

    df_asesor["Asesor"] = (
        df_asesor["Asesor"]
        .apply(limpiar_nombre)
    )

    df_asesor["% RETE CTA"] = (
        df_asesor["% RETE CTA"]
        .apply(convertir_porcentaje)
    )

    df_asesor["Beneficio"] = (
        df_asesor["Beneficio"]
        .apply(convertir_porcentaje)
    )


    # ========================================================
    # HOJA: RESUMEN RETES
    # ========================================================

    df_resumen = pd.read_excel(
        archivo,
        sheet_name=HOJA_RESUMEN
    )

    df_resumen.columns = [
        str(col).strip()
        for col in df_resumen.columns
    ]

    columnas_resumen = [
        "Asesor",
        "Retes Positivas",
        "Retes Negativas",
        "Total Retenciones"
    ]

    for columna in columnas_resumen:

        if columna not in df_resumen.columns:

            raise ValueError(
                f"La hoja '{HOJA_RESUMEN}' "
                f"no contiene la columna "
                f"'{columna}'."
            )

    df_resumen["Asesor"] = (
        df_resumen["Asesor"]
        .apply(limpiar_nombre)
    )

    df_resumen["Retes Positivas"] = (
        pd.to_numeric(
            df_resumen["Retes Positivas"],
            errors="coerce"
        )
        .fillna(0)
    )

    df_resumen["Retes Negativas"] = (
        pd.to_numeric(
            df_resumen["Retes Negativas"],
            errors="coerce"
        )
        .fillna(0)
    )

    df_resumen["Total Retenciones"] = (
        pd.to_numeric(
            df_resumen["Total Retenciones"],
            errors="coerce"
        )
        .fillna(0)
    )


    # ========================================================
    # BUSCAR TOTALES GENERALES
    # ========================================================

    total_grupo = df_grupo[
        df_grupo["GRUPO"]
        .apply(es_total)
    ]

    total_asesor = df_asesor[
        df_asesor["Asesor"]
        .apply(es_total)
    ]

    total_resumen = df_resumen[
        df_resumen["Asesor"]
        .apply(es_total)
    ]


    # ========================================================
    # TOTAL DE RETES X GRUPO
    # ========================================================

    if not total_grupo.empty:

        fila_total_grupo = (
            total_grupo.iloc[0]
        )

        total_rete_cta = float(
            fila_total_grupo["% RETE CTA"]
        )

        total_beneficio = float(
            fila_total_grupo["Beneficio"]
        )

    elif not total_asesor.empty:

        fila_total_asesor = (
            total_asesor.iloc[0]
        )

        total_rete_cta = float(
            fila_total_asesor["% RETE CTA"]
        )

        total_beneficio = float(
            fila_total_asesor["Beneficio"]
        )

    else:

        total_rete_cta = 0.0
        total_beneficio = 0.0


    # ========================================================
    # TOTAL DE RESUMEN RETES
    # ========================================================

    if not total_resumen.empty:

        fila_total_resumen = (
            total_resumen.iloc[0]
        )

        total_positivas = int(
            fila_total_resumen[
                "Retes Positivas"
            ]
        )

        total_negativas = int(
            fila_total_resumen[
                "Retes Negativas"
            ]
        )

        total_retenciones = int(
            fila_total_resumen[
                "Total Retenciones"
            ]
        )

    else:

        total_positivas = 0
        total_negativas = 0
        total_retenciones = 0


    # ========================================================
    # DEVOLVER TODOS LOS DATOS
    # ========================================================

    return {

        "grupo": df_grupo,

        "asesor": df_asesor,

        "resumen": df_resumen,

        "total": {

            "rete_cta": total_rete_cta,

            "beneficio": total_beneficio,

            "positivas": total_positivas,

            "negativas": total_negativas,

            "retenciones": total_retenciones
        }
    }


# ============================================================
# OBTENER TOTALES PARA APP.PY
# ============================================================

def obtener_totales():

    datos = leer_retenciones()

    return {

        "rete_cta":
            datos["total"]["rete_cta"],

        "beneficio":
            datos["total"]["beneficio"],

        "positivas":
            datos["total"]["positivas"],

        "negativas":
            datos["total"]["negativas"],

        "retenciones":
            datos["total"]["retenciones"]
    }


def obtener_datos_retenciones_totales():
    """
    Función de compatibilidad utilizada por app.py.

    Devuelve los porcentajes generales y el volumen
    total de retenciones.
    """

    datos = obtener_totales()

    volumen = obtener_volumen_total_retenciones_desde_resumen(
        ARCHIVO_EXCEL
    )

    return {

        "rete_cta":
            datos["rete_cta"],

        "beneficio":
            datos["beneficio"],

        "volumen":
            volumen
    }


# ============================================================
# VOLUMEN TOTAL DESDE RESUMEN
# ============================================================

def obtener_volumen_total_retenciones_desde_resumen(
    filepath
):

    df = cargar_hoja_excel(
        filepath,
        HOJA_RESUMEN
    )

    if df is None or df.empty:
        return 0

    col_asesor = buscar_columna_asesor(df)

    if col_asesor is None:
        col_asesor = df.columns[0]

    # --------------------------------------------------------
    # Buscar fila TOTAL
    # --------------------------------------------------------

    fila_total = None

    for _, fila in df.iterrows():

        if es_fila_total(
            fila[col_asesor]
        ):

            fila_total = fila
            break

    # --------------------------------------------------------
    # Detectar columnas numéricas
    # --------------------------------------------------------

    columnas_numericas = []

    for columna in df.columns:

        if columna == col_asesor:
            continue

        valores = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

        if valores.notna().sum() > 0:

            columnas_numericas.append(
                columna
            )

    # --------------------------------------------------------
    # Si existe TOTAL, buscar una columna de volumen
    # --------------------------------------------------------

    if fila_total is not None:

        posibles_total = [

            c
            for c in columnas_numericas

            if any(

                k in str(c).lower()

                for k in [
                    "total",
                    "volumen",
                    "cantidad",
                    "retencion",
                    "retes"
                ]
            )
        ]

        if posibles_total:

            valor = pd.to_numeric(
                fila_total[
                    posibles_total[0]
                ],
                errors="coerce"
            )

            if pd.notna(valor):

                return int(valor)

    # --------------------------------------------------------
    # Si no hay columna TOTAL clara,
    # sumar columnas numéricas de asesores.
    # --------------------------------------------------------

    df_sin_total = df.copy()

    df_sin_total = df_sin_total[
        ~df_sin_total[col_asesor]
        .apply(es_fila_total)
    ]

    if columnas_numericas:

        suma = 0

        for columna in columnas_numericas:

            valores = pd.to_numeric(
                df_sin_total[columna],
                errors="coerce"
            )

            suma += valores.sum()

        return int(suma)

    return 0


# ============================================================
# OBTENER DATOS DE UN ASESOR
# ============================================================

def obtener_asesor(nombre_asesor):

    datos = leer_retenciones()

    nombre_buscado = (
        limpiar_nombre(
            nombre_asesor
        )
        .lower()
    )

    df_asesores = datos["asesor"]

    df_resumen = datos["resumen"]

    # --------------------------------------------------------
    # Buscar porcentajes del asesor
    # --------------------------------------------------------

    coincidencia_asesor = (
        df_asesores[
            df_asesores["Asesor"]
            .str.lower()
            == nombre_buscado
        ]
    )

    # --------------------------------------------------------
    # Buscar cantidades
    # --------------------------------------------------------

    coincidencia_resumen = (
        df_resumen[
            df_resumen["Asesor"]
            .str.lower()
            == nombre_buscado
        ]
    )

    resultado = {

        "asesor":
            nombre_asesor,

        "rete_cta":
            0.0,

        "beneficio":
            0.0,

        "positivas":
            0,

        "negativas":
            0,

        "retenciones":
            0
    }

    if not coincidencia_asesor.empty:

        fila = coincidencia_asesor.iloc[0]

        resultado["rete_cta"] = float(
            fila["% RETE CTA"]
        )

        resultado["beneficio"] = float(
            fila["Beneficio"]
        )

    if not coincidencia_resumen.empty:

        fila = coincidencia_resumen.iloc[0]

        resultado["positivas"] = int(
            fila["Retes Positivas"]
        )

        resultado["negativas"] = int(
            fila["Retes Negativas"]
        )

        resultado["retenciones"] = int(
            fila["Total Retenciones"]
        )

    return resultado


# ============================================================
# DATOS POR GRUPO
# ============================================================

def obtener_grupos():

    datos = leer_retenciones()

    df = datos["grupo"]

    resultado = {}

    for _, fila in df.iterrows():

        grupo = fila["GRUPO"]

        resultado[grupo] = {

            "rete_cta":
                float(
                    fila["% RETE CTA"]
                ),

            "beneficio":
                float(
                    fila["Beneficio"]
                )
        }

    return resultado


# ============================================================
# DATOS DE TODOS LOS ASESORES
# ============================================================

def obtener_asesores():

    datos = leer_retenciones()

    df_asesores = datos["asesor"]

    df_resumen = datos["resumen"]

    resultado = {}

    for _, fila in df_asesores.iterrows():

        nombre = fila["Asesor"]

        if not nombre:
            continue

        resultado[nombre] = {

            "rete_cta":
                float(
                    fila["% RETE CTA"]
                ),

            "beneficio":
                float(
                    fila["Beneficio"]
                ),

            "positivas":
                0,

            "negativas":
                0,

            "retenciones":
                0
        }

    # --------------------------------------------------------
    # Agregar cantidades del resumen
    # --------------------------------------------------------

    for _, fila in df_resumen.iterrows():

        nombre = fila["Asesor"]

        if not nombre:
            continue

        if nombre not in resultado:

            resultado[nombre] = {

                "rete_cta":
                    0.0,

                "beneficio":
                    0.0,

                "positivas":
                    0,

                "negativas":
                    0,

                "retenciones":
                    0
            }

        resultado[nombre]["positivas"] = int(
            fila["Retes Positivas"]
        )

        resultado[nombre]["negativas"] = int(
            fila["Retes Negativas"]
        )

        resultado[nombre]["retenciones"] = int(
            fila["Total Retenciones"]
        )

    return resultado


# ============================================================
# FILTRADO FLEXIBLE DE ASESORES
# ============================================================

def filtrar_por_asesor_flexible(
    df,
    asesor_objetivo
):

    if df is None or df.empty:
        return pd.DataFrame()

    if not asesor_objetivo:
        return pd.DataFrame()

    asesor_objetivo = (
        str(asesor_objetivo)
        .strip()
    )

    # --------------------------------------------------------
    # Buscar directamente en el índice
    # --------------------------------------------------------

    match_idx = df[
        df.index
        .astype(str)
        .str.contains(
            asesor_objetivo,
            case=False,
            na=False
        )
    ]

    if not match_idx.empty:
        return match_idx

    # --------------------------------------------------------
    # Separar partes del nombre
    # --------------------------------------------------------

    partes = [

        p.strip()

        for p in (
            asesor_objetivo
            .replace(",", "")
            .split()
        )

        if len(p.strip()) > 2
    ]

    # --------------------------------------------------------
    # Buscar columnas candidatas
    # --------------------------------------------------------

    cols_candidatas = [

        c

        for c in df.columns

        if any(

            k in str(c).lower()

            for k in [
                "asesor",
                "nombre",
                "agente",
                "etiqueta",
                "fila"
            ]
        )
    ]

    if cols_candidatas:

        for col in cols_candidatas:

            res = df[
                df[col]
                .astype(str)
                .str.contains(
                    asesor_objetivo,
                    case=False,
                    na=False
                )
            ]

            if not res.empty:
                return res

            if partes:

                res_parcial = df[
                    df[col]
                    .astype(str)
                    .str.contains(
                        partes[0],
                        case=False,
                        na=False
                    )
                ]

                if not res_parcial.empty:
                    return res_parcial

    # --------------------------------------------------------
    # Búsqueda general en toda la tabla
    # --------------------------------------------------------

    mask = (

        df.astype(str)
        .apply(

            lambda x:

            x.str.contains(
                asesor_objetivo,
                case=False,
                na=False
            )
        )
        .any(axis=1)
    )

    res_gen = df[mask]

    if not res_gen.empty:
        return res_gen

    # --------------------------------------------------------
    # Búsqueda parcial
    # --------------------------------------------------------

    if partes:

        mask_parcial = (

            df.astype(str)
            .apply(

                lambda x:

                x.str.contains(
                    partes[0],
                    case=False,
                    na=False
                )
            )
            .any(axis=1)
        )

        return df[mask_parcial]

    return pd.DataFrame()


# ============================================================
# PRUEBA DEL MÓDULO
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PRUEBA DEL MÓDULO DE RETENCIONES")
    print("=" * 60)

    try:

        datos = leer_retenciones()

        print()
        print("DATOS GENERALES")
        print("-" * 60)

        print(
            f"% RETE CTA : "
            f"{datos['total']['rete_cta'] * 100:.2f}%"
        )

        print(
            f"Beneficio  : "
            f"{datos['total']['beneficio'] * 100:.2f}%"
        )

        print(
            f"Positivas  : "
            f"{datos['total']['positivas']}"
        )

        print(
            f"Negativas  : "
            f"{datos['total']['negativas']}"
        )

        print(
            f"Total      : "
            f"{datos['total']['retenciones']}"
        )

        print()
        print("GRUPOS")
        print("-" * 60)

        for grupo, valores in obtener_grupos().items():

            print(
                f"{grupo}: "
                f"Rete CTA "
                f"{valores['rete_cta'] * 100:.2f}% | "
                f"Beneficio "
                f"{valores['beneficio'] * 100:.2f}%"
            )

        print()
        print("ASESORES")
        print("-" * 60)

        asesores = obtener_asesores()

        for nombre, valores in asesores.items():

            print(
                f"{nombre}: "
                f"Rete CTA "
                f"{valores['rete_cta'] * 100:.2f}% | "
                f"Beneficio "
                f"{valores['beneficio'] * 100:.2f}% | "
                f"Pos "
                f"{valores['positivas']} | "
                f"Neg "
                f"{valores['negativas']} | "
                f"Total "
                f"{valores['retenciones']}"
            )

        print()
        print("=" * 60)
        print(
            "MÓDULO DE RETENCIONES "
            "FUNCIONANDO CORRECTAMENTE"
        )
        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(error)