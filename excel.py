import pandas as pd


def obtener_hojas(ruta_excel):
    """
    Devuelve una lista con los nombres de todas las hojas
    que existen dentro del archivo Excel.
    """
    archivo = pd.ExcelFile(ruta_excel)
    return archivo.sheet_names


def inspeccionar_hoja(ruta_excel, nombre_hoja):
    """
    Lee una hoja del Excel y muestra información básica
    sobre su estructura.
    """
    df = pd.read_excel(ruta_excel, sheet_name=nombre_hoja)

    print()
    print("=" * 60)
    print(f"HOJA: {nombre_hoja}")
    print("=" * 60)

    print()
    print("COLUMNAS:")
    for columna in df.columns:
        print("-", columna)

    print()
    print("PRIMERAS FILAS:")
    print(df.head(5).to_string(index=False))

    print()
    print(f"Cantidad de filas: {len(df)}")
    print("=" * 60)


def identificar_totales(ruta_excel):
    """
    Busca las filas 'Total general' en las hojas de Retenciones.
    """

    hojas = [
        "Retes X grupo",
        "Retes X asesor",
        "Resumen Retes"
    ]

    for hoja in hojas:

        df = pd.read_excel(
            ruta_excel,
            sheet_name=hoja
        )

        print()
        print("=" * 60)
        print(f"TOTAL DE: {hoja}")
        print("=" * 60)

        primera_columna = df.columns[0]

        totales = df[
            df[primera_columna]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("total general")
        ]

        if totales.empty:
            print("No se encontró 'Total general'.")
        else:
            print(totales.to_string(index=False))