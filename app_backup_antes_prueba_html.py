import io
import os
import time
import pandas as pd
import streamlit as st

from retenciones import (
    obtener_datos_retenciones_totales,
    cargar_hoja_excel,
    buscar_columna_rete_cta,
    buscar_columna_beneficio,
    filtrar_por_asesor_flexible,
    formatear_porcentaje,
    normalizar_porcentaje,
)

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE STREAMLIT
# ==========================================
# Los parámetros de página deben establecerse antes
# de cualquier otro comando visual de Streamlit.

query_params = st.query_params
modo_tv_externo = query_params.get("vista") == "tv"

if modo_tv_externo:
    st.set_page_config(
        page_title="Cardinal // Wallboard TV",
        page_icon="📺",
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="Cardinal // Panel General",
        page_icon="🧭",
        layout="wide"
    )


# ==========================================
# 2. BASE DE DATOS DE USUARIOS Y CREDENCIALES
# ==========================================
USUARIOS_PERFILES = {
    "admin": {
        "password": "cardinal2026",
        "rol": "admin",
        "nombre_asesor": None,
        "nombre_mostrar": "Sky Cruiser (Administrador)",
    },
    "erika.aguirre": {
        "password": "123",
        "rol": "asesor",
        "nombre_asesor": "AGUIRRE, ERIKA ALEJANDRA",
        "nombre_mostrar": "Erika Aguirre",
    },
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None

if "rol_actual" not in st.session_state:
    st.session_state["rol_actual"] = None


# ==========================================
# 3. OBJETIVOS OFICIALES
# ==========================================
OBJETIVOS = {
    "rete_pct": 0.70,
    "beneficio_pct": 0.45,
    "ventas_grupal": 260,
    "ventas_individual": 10,
    "nps_pct": 0.65,
}


# ==========================================
# 4. FUNCIONES GENERALES
# ==========================================

def calcular_semaforo(valor_actual, valor_objetivo):
    """
    Retorna:
    (color_hex, etiqueta_estado, clase_css)
    """

    if valor_objetivo == 0:
        return "#8b949e", "Sin Meta", "sem-gris"

    cumplimiento = valor_actual / valor_objetivo

    if cumplimiento >= 1.0:
        return "#3fb950", "¡Cumplido!", "sem-verde"

    elif cumplimiento >= 0.85:
        return "#f59e0b", "Cerca", "sem-amarillo"

    else:
        return "#f85149", "Alerta", "sem-rojo"


# ==========================================
# 8. PODIO
# ==========================================

def obtener_top_podio(
    filepath,
    sheet_name,
    col_criterio_busqueda,
    es_porcentaje=False,
    n=3
):

    if not os.path.exists(filepath):
        return []

    try:

        df = pd.read_excel(
            filepath,
            sheet_name=sheet_name
        )

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        col_asesor = buscar_columna_asesor(df)

        if col_asesor is None:
            col_asesor = df.columns[0]

        col_metrica = next(
            (
                c
                for c in df.columns
                if col_criterio_busqueda.lower()
                in str(c).lower()
            ),
            None
        )

        if not col_metrica:
            return []

        df_copia = df[
            [
                col_asesor,
                col_metrica
            ]
        ].dropna().copy()

        df_copia = df_copia[
            ~df_copia[col_asesor]
            .apply(es_fila_total)
        ]

        df_copia["val_num"] = (
            df_copia[col_metrica]
            .apply(convertir_numero)
        )

        df_copia = (
            df_copia
            .dropna(subset=["val_num"])
            .sort_values(
                by="val_num",
                ascending=False
            )
            .head(n)
        )

        resultado = []

        for _, row in df_copia.iterrows():

            val_num = row["val_num"]

            if es_porcentaje:

                if val_num > 1:
                    val_num = val_num / 100

                val_str = (
                    f"{val_num * 100:.1f}%"
                )

            else:

                if float(val_num).is_integer():
                    val_str = f"{int(val_num):,}"

                else:
                    val_str = f"{val_num:.2f}"

            resultado.append(
                (
                    str(
                        row[col_asesor]
                    ).strip(),
                    val_str
                )
            )

        return resultado

    except Exception as e:

        print(
            f"Error en podio: {e}"
        )

        return []


def calcular_podio_general(n=3):

    dict_puntajes = {}

    def procesar_archivo_para_ranking(
        filepath,
        sheet,
        criterio
    ):

        if not os.path.exists(filepath):
            return

        try:

            df = pd.read_excel(
                filepath,
                sheet_name=sheet
            )

            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            col_as = buscar_columna_asesor(df)

            if col_as is None:
                col_as = df.columns[0]

            col_met = next(
                (
                    c
                    for c in df.columns
                    if criterio.lower()
                    in str(c).lower()
                ),
                None
            )

            if not col_met:
                return

            sub = df[
                [
                    col_as,
                    col_met
                ]
            ].dropna().copy()

            sub = sub[
                ~sub[col_as]
                .apply(es_fila_total)
            ]

            sub["num"] = (
                sub[col_met]
                .apply(convertir_numero)
            )

            sub = sub.dropna(
                subset=["num"]
            )

            if sub.empty:
                return

            max_val = sub["num"].max()

            if max_val <= 0:
                return

            for _, r in sub.iterrows():

                asesor_norm = (
                    str(
                        r[col_as]
                    )
                    .strip()
                    .upper()
                )

                score = (
                    r["num"]
                    / max_val
                ) * 100

                if asesor_norm not in dict_puntajes:
                    dict_puntajes[
                        asesor_norm
                    ] = []

                dict_puntajes[
                    asesor_norm
                ].append(score)

        except Exception as e:

            print(
                f"Error procesando ranking: {e}"
            )

    procesar_archivo_para_ranking(
        "datos_retenciones.xlsx",
        "Retes X Asesor",
        "rete"
    )

    procesar_archivo_para_ranking(
        "datos_ventas.xlsx",
        "Ventas X asesor",
        "total"
    )

    procesar_archivo_para_ranking(
        "datos_nps.xlsx",
        "NPS X asesor",
        "satisf"
    )

    promedios_globales = [
        (
            asesor,
            sum(scores) / len(scores)
        )
        for asesor, scores
        in dict_puntajes.items()
        if len(scores) > 0
    ]

    promedios_globales.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return promedios_globales[:n]


# ==========================================
# 9. HTML DE MÉTRICAS
# ==========================================

def render_metric_html(
    label,
    value,
    meta_txt,
    estado_txt,
    color_sem
):

    return f"""
    <div class="metric-card"
         style="border-top: 3px solid {color_sem};">

        <div style="
            font-size: 10px;
            color: #8b949e;
            text-transform: uppercase;
            font-weight: 600;
        ">
            {label}
        </div>

        <div style="
            font-size: 18px;
            font-weight: 700;
            color: #f0f6fc;
            margin-top: 3px;
        ">
            {value}

            <span style="
                font-size:11px;
                color:#8b949e;
            ">
                (Meta: {meta_txt})
            </span>
        </div>

        <div style="
            margin-top: 4px;
            font-size: 11px;
            font-weight: 800;
            color: {color_sem};
        ">
            ● {estado_txt}
        </div>

    </div>
    """


# ==========================================
# 10. MODO WALLBOARD TV
# ==========================================

if modo_tv_externo:

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #0e1117;
            color: #e6edf3;
        }

        .tv-card {
            background: linear-gradient(
                135deg,
                #161b22 0%,
                #0d1117 100%
            );

            border: 1px solid #30363d;
            border-top: 4px solid #10b981;

            padding: 24px;
            border-radius: 16px;

            text-align: center;

            box-shadow:
                0 8px 24px rgba(0, 0, 0, 0.5);

            margin-bottom: 15px;
        }

        .tv-title {
            font-size: 15px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 700;
        }

        .tv-value {
            font-size: 42px;
            font-weight: 800;
            color: #f3f4f6;
            margin: 10px 0;
        }

        .podium-container {
            background: linear-gradient(
                135deg,
                #161b22 0%,
                #0d1117 100%
            );

            border: 1px solid #30363d;
            border-top: 4px solid #3b82f6;

            padding: 20px;
            border-radius: 16px;

            box-shadow:
                0 8px 24px rgba(0, 0, 0, 0.5);

            margin-bottom: 15px;
            height: 100%;
        }

        .podium-title {
            font-size: 16px;
            color: #f3f4f6;

            text-transform: uppercase;
            letter-spacing: 1.5px;

            font-weight: 800;

            margin-bottom: 15px;

            text-align: center;

            border-bottom: 1px solid #30363d;

            padding-bottom: 10px;
        }

        .podium-item {
            background-color: #0d1117;

            border: 1px solid #30363d;

            padding: 10px 15px;

            border-radius: 8px;

            margin-bottom: 8px;

            display: flex;

            justify-content: space-between;

            align-items: center;
        }

        .podium-gold {
            border-left: 4px solid #f59e0b;
        }

        .podium-silver {
            border-left: 4px solid #94a3b8;
        }

        .podium-bronze {
            border-left: 4px solid #b45309;
        }

        .general-podium-box {
            background: linear-gradient(
                135deg,
                #1f2937 0%,
                #111827 100%
            );

            border: 2px solid #f59e0b;

            border-radius: 16px;

            padding: 25px;

            box-shadow:
                0 10px 30px
                rgba(245, 158, 11, 0.2);

            margin-top: 20px;
        }

        .prize-tag {
            background-color:
                rgba(245, 158, 11, 0.15);

            color: #fcd34d;

            padding: 4px 10px;

            border-radius: 6px;

            font-size: 12px;

            font-weight: 700;

            border:
                1px solid
                rgba(245, 158, 11, 0.4);
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
            text-align: center;
            margin-bottom: 25px;
            margin-top: 10px;
        ">

            <h1 style="
                color: #f3f4f6;
                font-weight: 800;
                letter-spacing: 2px;
            ">
                🟢 WALLBOARD EN VIVO //
                TORRE DE CONTROL CALL CENTER
            </h1>

            <p style="
                color: #9ca3af;
                font-size: 15px;
            ">
                Monitoreo corporativo en tiempo real
                y cumplimiento de metas operativas.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # DATOS DEL WALLBOARD
    # ==========================================

    datos_ret = obtener_datos_retenciones_totales()

    total_ret_volumen = datos_ret["volumen"]

    rete_global_pct = (
        datos_ret["rete_cta"]
        if datos_ret["rete_cta"] is not None
        else 0.0
    )

    beneficio_global_pct = (
        datos_ret["beneficio"]
        if datos_ret["beneficio"] is not None
        else 0.0
    )

    total_ven_count = 0

    if os.path.exists(
        "datos_ventas.xlsx"
    ):

        try:

            df_ventas_tv = pd.read_excel(
                "datos_ventas.xlsx",
                sheet_name="Ventas X asesor"
            )

            total_ven_count = len(
                df_ventas_tv
            )

        except:
            total_ven_count = 0

    df_nps_tv = None

    if os.path.exists(
        "datos_nps.xlsx"
    ):

        try:

            df_nps_tv = pd.read_excel(
                "datos_nps.xlsx",
                sheet_name="NPS X asesor"
            )

        except:
            df_nps_tv = None

    nps_positivo_pct = (
        calcular_porcentaje_nps_positivo(
            df_nps_tv
        )
    )

    # ==========================================
    # SEMÁFOROS
    # ==========================================

    col_r_sem, label_r_sem, _ = calcular_semaforo(
        rete_global_pct,
        OBJETIVOS["rete_pct"]
    )

    col_b_sem, label_b_sem, _ = calcular_semaforo(
        beneficio_global_pct,
        OBJETIVOS["beneficio_pct"]
    )

    col_v_sem, label_v_sem, _ = calcular_semaforo(
        total_ven_count,
        OBJETIVOS["ventas_grupal"]
    )

    col_n_sem, label_n_sem, _ = calcular_semaforo(
        nps_positivo_pct,
        OBJETIVOS["nps_pct"]
    )

    # ==========================================
    # MÉTRICAS PRINCIPALES
    # ==========================================

    t_col1, t_col2, t_col3, t_col4 = st.columns(4)

    with t_col1:

        st.markdown(
            f"""
            <div class="tv-card"
                 style="border-top-color:{col_r_sem};">

                <div class="tv-title">
                    📌 % RETE CTA
                </div>

                <div class="tv-value"
                     style="color:{col_r_sem};">
                    {rete_global_pct * 100:.1f}%
                </div>

                <div style="
                    color:{col_r_sem};
                    font-size:14px;
                    font-weight:800;
                ">
                    ● Estado: {label_r_sem}
                </div>

                <div style="
                    color:#9ca3af;
                    font-size:12px;
                    margin-top:6px;
                ">
                    Meta:
                    {OBJETIVOS["rete_pct"] * 100:.0f}%
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with t_col2:

        st.markdown(
            f"""
            <div class="tv-card"
                 style="border-top-color:{col_b_sem};">

                <div class="tv-title">
                    📌 % BENEFICIO
                </div>

                <div class="tv-value"
                     style="color:{col_b_sem};">
                    {beneficio_global_pct * 100:.1f}%
                </div>

                <div style="
                    color:{col_b_sem};
                    font-size:14px;
                    font-weight:800;
                ">
                    ● Estado: {label_b_sem}
                </div>

                <div style="
                    color:#9ca3af;
                    font-size:12px;
                    margin-top:6px;
                ">
                    Meta:
                    {OBJETIVOS["beneficio_pct"] * 100:.0f}%
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with t_col3:

        st.markdown(
            f"""
            <div class="tv-card"
                 style="border-top-color:{col_v_sem};">

                <div class="tv-title">
                    💰 TOTAL VENTAS
                </div>

                <div class="tv-value"
                     style="color:{col_v_sem};">
                    {total_ven_count:,}
                </div>

                <div style="
                    color:{col_v_sem};
                    font-size:14px;
                    font-weight:800;
                ">
                    ● Estado: {label_v_sem}
                </div>

                <div style="
                    color:#9ca3af;
                    font-size:12px;
                    margin-top:6px;
                ">
                    Meta:
                    {OBJETIVOS["ventas_grupal"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with t_col4:

        st.markdown(
            f"""
            <div class="tv-card"
                 style="border-top-color:{col_n_sem};">

                <div class="tv-title">
                    ⭐ NPS POSITIVO
                </div>

                <div class="tv-value"
                     style="color:{col_n_sem};">
                    {nps_positivo_pct * 100:.1f}%
                </div>

                <div style="
                    color:{col_n_sem};
                    font-size:14px;
                    font-weight:800;
                ">
                    ● Estado: {label_n_sem}
                </div>

                <div style="
                    color:#9ca3af;
                    font-size:12px;
                    margin-top:6px;
                ">
                    Meta:
                    {OBJETIVOS["nps_pct"] * 100:.0f}%
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================================
    # PODIOS
    # ==========================================

    st.markdown(
        """
        <h3 style="
            text-align:center;
            color:#f3f4f6;
            margin-top:15px;
            margin-bottom:15px;
        ">
            🏆 PODIO DE RENDIMIENTO //
            TOP 3 POR CATEGORÍA
        </h3>
        """,
        unsafe_allow_html=True
    )

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    classes = [
        "podium-gold",
        "podium-silver",
        "podium-bronze"
    ]

    cats_data = [

        (
            "📌 Top % Rete CTA",
            "datos_retenciones.xlsx",
            "Retes X Asesor",
            "rete",
            True,
            p_col1,
            "#3fb950"
        ),

        (
            "📌 Top % Beneficio",
            "datos_retenciones.xlsx",
            "Retes X Asesor",
            "benefic",
            True,
            p_col2,
            "#10b981"
        ),

        (
            "💰 Top Ventas",
            "datos_ventas.xlsx",
            "Ventas X asesor",
            "total",
            False,
            p_col3,
            "#3b82f6"
        ),

        (
            "⭐ Top NPS",
            "datos_nps.xlsx",
            "NPS X asesor",
            "satisf",
            True,
            p_col4,
            "#f59e0b"
        )
    ]

    for (
        title,
        fpath,
        sheet,
        crit,
        is_pct,
        col_obj,
        color
    ) in cats_data:

        top_res = obtener_top_podio(
            fpath,
            sheet,
            crit,
            is_pct
        )

        with col_obj:

            html = (
                f"""
                <div class="podium-container"
                     style="border-top-color:{color};">

                    <div class="podium-title">
                        {title}
                    </div>
                """
            )

            if top_res:

                for idx, (
                    asesor,
                    val
                ) in enumerate(
                    top_res[:3]
                ):

                    html += (
                        f"""
                        <div class="podium-item
                                    {classes[idx]}">

                            <span style="
                                font-size:12px;
                                font-weight:bold;
                            ">
                                {medals[idx]}
                                {asesor}
                            </span>

                            <span style="
                                color:{color};
                                font-weight:800;
                                font-size:13px;
                            ">
                                {val}
                            </span>

                        </div>
                        """
                    )

            else:

                html += (
                    """
                    <p style="
                        color:#8b949e;
                        font-size:12px;
                        text-align:center;
                    ">
                        Sin datos
                    </p>
                    """
                )

            html += "</div>"

            st.markdown(
                html,
                unsafe_allow_html=True
            )

    # ==========================================
    # PODIO GENERAL
    # ==========================================

    top_general = calcular_podio_general(3)

    st.markdown(
        """
        <div class="general-podium-box">

            <div style="
                text-align:center;
                margin-bottom:20px;
            ">

                <h2 style="
                    color:#fcd34d;
                    font-weight:800;
                    letter-spacing:2px;
                    margin:0;
                ">
                    👑 PODIO GENERAL DE EXCELENCIA //
                    TOP 3 DEL CALL CENTER
                </h2>

                <p style="
                    color:#9ca3af;
                    font-size:13px;
                    margin-top:5px;
                ">
                    Evaluación combinada de
                    Retenciones, Ventas y NPS
                    con premios oficiales de la operación.
                </p>

            </div>
        """,
        unsafe_allow_html=True
    )

    g_col1, g_col2, g_col3 = st.columns(3)

    premios_texto = [

        (
            "🥇 1er Puesto",
            "Un día Libre",
            "podium-gold",
            "#f59e0b"
        ),

        (
            "🥈 2do Puesto",
            "Una hamburguesa",
            "podium-silver",
            "#94a3b8"
        ),

        (
            "🥉 3er Puesto",
            "Recarga de $10.000 para la SUBE",
            "podium-bronze",
            "#b45309"
        )
    ]

    for idx, col_obj in enumerate(
        [
            g_col1,
            g_col2,
            g_col3
        ]
    ):

        (
            puesto_label,
            premio_desc,
            clase_css,
            color_borde
        ) = premios_texto[idx]

        if idx < len(top_general):

            asesor_nombre = top_general[idx][0]

            score_val = (
                f"Score: "
                f"{top_general[idx][1]:.1f} pts"
            )

        else:

            asesor_nombre = "Sin asignar"
            score_val = "---"

        with col_obj:

            st.markdown(
                f"""
                <div class="
                    podium-item
                    {clase_css}
                "
                style="
                    background-color:#0d1117;
                    padding:16px;
                    border-radius:12px;
                    border-left:
                        5px solid {color_borde};
                    flex-direction:column;
                    align-items:flex-start;
                ">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        width:100%;
                        align-items:center;
                        margin-bottom:8px;
                    ">

                        <span style="
                            font-size:14px;
                            font-weight:800;
                            color:{color_borde};
                        ">
                            {puesto_label}
                        </span>

                        <span style="
                            font-size:11px;
                            color:#8b949e;
                        ">
                            {score_val}
                        </span>

                    </div>

                    <div style="
                        font-size:15px;
                        font-weight:700;
                        color:#f3f4f6;
                        margin-bottom:10px;
                        width:100%;
                        white-space:nowrap;
                        overflow:hidden;
                        text-overflow:ellipsis;
                    ">
                        {asesor_nombre}
                    </div>

                    <div style="
                        width:100%;
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        border-top:
                            1px solid #30363d;
                        padding-top:8px;
                    ">

                        <span style="
                            font-size:11px;
                            color:#9ca3af;
                            text-transform:uppercase;
                        ">
                            Premio:
                        </span>

                        <span class="prize-tag">
                            🎁 {premio_desc}
                        </span>

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.stop()


# ==========================================
# 11. LOGIN
# ==========================================

if not st.session_state["autenticado"]:

    st.markdown(
        """
        <style>

        .stApp {
            background-color:#0e1117;
            color:#e6edf3;
        }

        .login-box {
            background-color:#161b22;

            border:1px solid #30363d;

            padding:30px;

            border-radius:12px;

            box-shadow:
                0 4px 12px
                rgba(0,0,0,0.4);

            max-width:400px;

            margin:80px auto;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
            text-align:center;
        ">

            <h2>
                🧭 PROYECTO CARDINAL
            </h2>

            <p style="
                color:#8b949e;
                font-size:14px;
            ">
                Torre de Control Operativa
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("form_login"):

        user_input = st.text_input(
            "Usuario",
            placeholder="ej. admin o erika.aguirre"
        )

        pass_input = st.text_input(
            "Contraseña",
            type="password",
            placeholder="••••••••"
        )

        submit_login = st.form_submit_button(
            "Ingresar al Sistema",
            use_container_width=True
        )

        if submit_login:

            if (
                user_input in USUARIOS_PERFILES
                and
                USUARIOS_PERFILES[user_input]["password"]
                == pass_input
            ):

                st.session_state[
                    "autenticado"
                ] = True

                st.session_state[
                    "usuario_actual"
                ] = user_input

                st.session_state[
                    "rol_actual"
                ] = (
                    USUARIOS_PERFILES[
                        user_input
                    ]["rol"]
                )

                st.rerun()

            else:

                st.error(
                    "⚠️ Usuario o contraseña incorrectos."
                )

    st.stop()


# ==========================================
# 12. PANEL AUTENTICADO
# ==========================================

st.markdown(
    """
    <style>

    .stApp {
        background-color:#0e1117;
        color:#e6edf3;
    }

    @keyframes fadeInSlide {

        0% {
            opacity:0;
            transform:translateX(-15px);
        }

        100% {
            opacity:1;
            transform:translateX(0);
        }

    }

    .carousel-animated {
        animation:
            fadeInSlide
            0.6s
            cubic-bezier(
                0.16,
                1,
                0.3,
                1
            )
            forwards;
    }

    .cardinal-header {

        background:
            linear-gradient(
                90deg,
                #1f2937 0%,
                #111827 100%
            );

        border-left:
            4px solid #3b82f6;

        padding:15px 20px;

        border-radius:8px;

        margin-bottom:20px;

        box-shadow:
            0 4px 6px
            rgba(0,0,0,0.3);
    }

    .cardinal-title {

        font-size:24px;

        font-weight:800;

        color:#f3f4f6;

        margin:0;

        letter-spacing:1px;
    }

    .cardinal-subtitle {

        font-size:12px;

        color:#9ca3af;

        margin-top:3px;

        text-transform:uppercase;

        letter-spacing:2px;
    }

    .panel-box {

        background-color:#161b22;

        border:1px solid #30363d;

        border-top:
            3px solid #3b82f6;

        padding:15px;

        border-radius:12px;

        box-shadow:
            0 4px 12px
            rgba(0,0,0,0.3);

        margin-bottom:10px;
    }

    .panel-title {

        font-size:16px;

        font-weight:700;

        color:#f0f6fc;

        margin-bottom:12px;

        border-bottom:
            1px solid #30363d;

        padding-bottom:8px;

        display:flex;

        justify-content:space-between;

        align-items:center;
    }

    .metric-card {

        background-color:#0d1117;

        border:1px solid #30363d;

        padding:10px;

        border-radius:8px;

        text-align:center;

        box-shadow:
            0 2px 6px
            rgba(0,0,0,0.2);
    }

    .advisor-hero {

        background:
            linear-gradient(
                135deg,
                #1f2937 0%,
                #111827 100%
            );

        border:1px solid #374151;

        border-top:
            4px solid #10b981;

        border-radius:16px;

        padding:25px;

        margin-bottom:25px;

        box-shadow:
            0 10px 25px
            rgba(0,0,0,0.4);

        display:flex;

        justify-content:space-between;

        align-items:center;
    }

    </style>
    """,
    unsafe_allow_html=True
)

if "carrusel_retencion" not in st.session_state:
    st.session_state[
        "carrusel_retencion"
    ] = 0


user_info = USUARIOS_PERFILES[
    st.session_state["usuario_actual"]
]

es_admin = (
    st.session_state["rol_actual"]
    == "admin"
)


# ==========================================
# 13. SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        f"""
        ### 👤 Sesión:
        {user_info['nombre_mostrar']}
        """
    )

    if es_admin:

        st.markdown("---")

        st.markdown(
            "### 📂 Carga de Planillas (Admin)"
        )

        st.markdown(
            "Configuración centralizada de datos:"
        )

        file_ret_sub = st.file_uploader(
            "Subir Retenciones (.xlsx)",
            type=["xlsx"],
            key="up_ret"
        )

        if file_ret_sub is not None:

            with open(
                "datos_retenciones.xlsx",
                "wb"
            ) as f:

                f.write(
                    file_ret_sub.getbuffer()
                )

            st.success(
                "¡Retenciones actualizadas en disco!"
            )

        file_ven_sub = st.file_uploader(
            "Subir Ventas (.xlsx)",
            type=["xlsx"],
            key="up_ven"
        )

        if file_ven_sub is not None:

            with open(
                "datos_ventas.xlsx",
                "wb"
            ) as f:

                f.write(
                    file_ven_sub.getbuffer()
                )

            st.success(
                "¡Ventas actualizadas en disco!"
            )

        file_nps_sub = st.file_uploader(
            "Subir NPS (.xlsx)",
            type=["xlsx"],
            key="up_nps"
        )

        if file_nps_sub is not None:

            with open(
                "datos_nps.xlsx",
                "wb"
            ) as f:

                f.write(
                    file_nps_sub.getbuffer()
                )

            st.success(
                "¡NPS actualizado en disco!"
            )

    else:

        st.markdown(
            """
            ℹ️ *Vista de Asesor
            (Sin permisos de configuración)*
            """
        )

    st.markdown("---")

    if st.button(
        "🚪 Cerrar Sesión",
        use_container_width=True
    ):

        st.session_state[
            "autenticado"
        ] = False

        st.session_state[
            "usuario_actual"
        ] = None

        st.session_state[
            "rol_actual"
        ] = None

        st.rerun()


# ==========================================
# 14. ENCABEZADO
# ==========================================

st.markdown(
    f"""
    <div class="cardinal-header">

        <div class="cardinal-title">
            🧭 PROYECTO CARDINAL //
            PANEL OPERATIVO
        </div>

        <div class="cardinal-subtitle">
            Modo:
            {
                'Administración General'
                if es_admin
                else
                'Espacio Personal Asesor'
            }
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================
# 15. PANEL ADMINISTRADOR
# ==========================================

if es_admin:

    col_info_admin, col_btn_proyectar = st.columns(
        [3, 1]
    )

    with col_info_admin:

        st.markdown(
            "### 🎛️ Panel de Control y Gestión Operativa"
        )

    with col_btn_proyectar:

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <a href="?vista=tv"
               target="_blank"
               style="
                   display:inline-block;
                   width:100%;
                   background-color:#10b981;
                   color:white;
                   padding:10px 15px;
                   border-radius:8px;
                   text-align:center;
                   font-weight:bold;
                   text-decoration:none;
                   box-shadow:
                       0 4px 10px
                       rgba(16,185,129,0.3);
               ">
                📺 PROYECTAR WALLBOARD
            </a>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    col_ret, col_ventas, col_nps = st.columns(3)


    # ======================================
    # RETENCIONES ADMIN
    # ======================================

    with col_ret:

        st.markdown(
            '<div class="panel-box carousel-animated">',
            unsafe_allow_html=True
        )

        origen_ret = (
            "datos_retenciones.xlsx"
            if os.path.exists(
                "datos_retenciones.xlsx"
            )
            else None
        )

        if origen_ret is None:

            st.markdown(
                """
                <div class="panel-title">
                    📌 Retenciones
                    (Falta Archivo)
                </div>
                """,
                unsafe_allow_html=True
            )

            st.info(
                "⚠️ Sube "
                "'datos_retenciones.xlsx' "
                "en el panel lateral."
            )

        else:

            try:

                datos_ret = (
                    obtener_datos_retenciones_totales()
                )

                volumen_total_ret = (
                    datos_ret["volumen"]
                )

                rete_total = (
                    datos_ret["rete_cta"]
                    if datos_ret["rete_cta"]
                    is not None
                    else 0
                )

                beneficio_total = (
                    datos_ret["beneficio"]
                    if datos_ret["beneficio"]
                    is not None
                    else 0
                )

                # ----------------------------------
                # CARGA DE HOJAS
                # ----------------------------------

                df_resumen_retes = (
                    cargar_hoja_excel(
                        origen_ret,
                        "Resumen Retes"
                    )
                )

                df_retes_asesor = (
                    cargar_hoja_excel(
                        origen_ret,
                        "Retes X Asesor"
                    )
                )

                df_retes_grupo = (
                    cargar_hoja_excel(
                        origen_ret,
                        "Retes X grupo"
                    )
                )

                # ----------------------------------
                # CARRUSEL
                # ----------------------------------

                if (
                    st.session_state[
                        "carrusel_retencion"
                    ] == 0
                ):

                    titulo_seccion = (
                        "📌 Retenciones // "
                        "Resumen"
                    )

                    df_activo = (
                        df_resumen_retes
                        if df_resumen_retes
                        is not None
                        else pd.DataFrame()
                    )

                    tag_carrusel = (
                        "🔄 [1/3: Resumen]"
                    )

                elif (
                    st.session_state[
                        "carrusel_retencion"
                    ] == 1
                ):

                    titulo_seccion = (
                        "📌 Retenciones // "
                        "X Asesor"
                    )

                    df_activo = (
                        df_retes_asesor
                        if df_retes_asesor
                        is not None
                        else pd.DataFrame()
                    )

                    tag_carrusel = (
                        "🔄 [2/3: Asesor]"
                    )

                else:

                    titulo_seccion = (
                        "📌 Retenciones // "
                        "X Grupo"
                    )

                    df_activo = (
                        df_retes_grupo
                        if df_retes_grupo
                        is not None
                        else pd.DataFrame()
                    )

                    tag_carrusel = (
                        "🔄 [3/3: Grupo]"
                    )

                # ----------------------------------
                # FORMATO DE PORCENTAJES
                # ----------------------------------

                if not df_activo.empty:

                    for col in df_activo.columns:

                        nombre_col = (
                            str(col).lower()
                        )

                        if (
                            "%"
                            in str(col)
                            or
                            "rete"
                            in nombre_col
                            or
                            "benef"
                            in nombre_col
                            or
                            "porcentaje"
                            in nombre_col
                            or
                            "pct"
                            in nombre_col
                        ):

                            df_activo[col] = (
                                df_activo[col]
                                .apply(
                                    lambda x:
                                    formatear_porcentaje(x)
                                    if pd.notnull(x)
                                    else x
                                )
                            )

                st.markdown(
                    f"""
                    <div class="panel-title">

                        <span>
                            {titulo_seccion}
                        </span>

                        <span style="
                            font-size:10px;
                            color:#3b82f6;
                        ">
                            {tag_carrusel}
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ----------------------------------
                # MÉTRICAS RETENCIONES
                # ----------------------------------

                col_c1, col_c2, col_c3 = st.columns(3)

                c_rete_hex, st_rete_lbl, _ = (
                    calcular_semaforo(
                        rete_total,
                        OBJETIVOS[
                            "rete_pct"
                        ]
                    )
                )

                c_ben_hex, st_ben_lbl, _ = (
                    calcular_semaforo(
                        beneficio_total,
                        OBJETIVOS[
                            "beneficio_pct"
                        ]
                    )
                )

                with col_c1:

                    st.markdown(
                        render_metric_html(
                            "Vol. Total",
                            f"{volumen_total_ret:,}",
                            "N/A",
                            "Activo",
                            "#3fb950"
                        ),
                        unsafe_allow_html=True
                    )

                with col_c2:

                    st.markdown(
                        render_metric_html(
                            "% Rete CTA",
                            f"{rete_total * 100:.1f}%",
                            f"{OBJETIVOS['rete_pct'] * 100:.0f}%",
                            st_rete_lbl,
                            c_rete_hex
                        ),
                        unsafe_allow_html=True
                    )

                with col_c3:

                    st.markdown(
                        render_metric_html(
                            "% Beneficio",
                            f"{beneficio_total * 100:.1f}%",
                            f"{OBJETIVOS['beneficio_pct'] * 100:.0f}%",
                            st_ben_lbl,
                            c_ben_hex
                        ),
                        unsafe_allow_html=True
                    )

                st.markdown(
                    "<br>",
                    unsafe_allow_html=True
                )

                # ----------------------------------
                # BUSCADOR
                # ----------------------------------

                busq_ret = st.text_input(
                    "🔍 Buscar Retenciones:",
                    placeholder="Filtrar...",
                    key="b_ret_carrusel"
                )

                if (
                    busq_ret
                    and not df_activo.empty
                ):

                    df_activo_f = (
                        df_activo[
                            df_activo
                            .astype(str)
                            .apply(
                                lambda x:
                                x.str.contains(
                                    busq_ret,
                                    case=False,
                                    na=False
                                )
                            )
                            .any(axis=1)
                        ]
                    )

                else:

                    df_activo_f = df_activo

                st.dataframe(
                    df_activo_f,
                    use_container_width=True,
                    height=300
                )

            except Exception as e:

                st.error(
                    f"Error en retenciones: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ======================================
    # VENTAS ADMIN
    # ======================================

    with col_ventas:

        st.markdown(
            '<div class="panel-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="panel-title">💰 Ventas</div>',
            unsafe_allow_html=True
        )

        origen_ven = (
            "datos_ventas.xlsx"
            if os.path.exists(
                "datos_ventas.xlsx"
            )
            else None
        )

        if origen_ven is None:

            st.info(
                "⚠️ Sube "
                "'datos_ventas.xlsx' "
                "en el panel lateral."
            )

        else:

            try:

                df_ventas = pd.read_excel(
                    origen_ven,
                    sheet_name="Ventas X asesor"
                )

                total_v = len(
                    df_ventas
                )

                c_v_hex, st_v_lbl, _ = (
                    calcular_semaforo(
                        total_v,
                        OBJETIVOS[
                            "ventas_grupal"
                        ]
                    )
                )

                v1, v2, v3 = st.columns(3)

                with v1:

                    st.markdown(
                        render_metric_html(
                            "Totales",
                            f"{total_v:,}",
                            str(
                                OBJETIVOS[
                                    "ventas_grupal"
                                ]
                            ),
                            st_v_lbl,
                            c_v_hex
                        ),
                        unsafe_allow_html=True
                    )

                with v2:

                    st.markdown(
                        render_metric_html(
                            "Cumpl.",
                            f"{(
                                total_v
                                /
                                OBJETIVOS[
                                    'ventas_grupal'
                                ]
                            ) * 100:.1f}%",
                            "100%",
                            st_v_lbl,
                            c_v_hex
                        ),
                        unsafe_allow_html=True
                    )

                with v3:

                    st.markdown(
                        render_metric_html(
                            "Bajas",
                            "12%",
                            "0%",
                            "Normal",
                            "#3fb950"
                        ),
                        unsafe_allow_html=True
                    )

                st.markdown(
                    "<br>",
                    unsafe_allow_html=True
                )

                busq_ventas = st.text_input(
                    "🔍 Buscar Ventas:",
                    placeholder="Filtrar...",
                    key="b_ventas_excel"
                )

                if busq_ventas:

                    df_ventas_f = (
                        df_ventas[
                            df_ventas
                            .astype(str)
                            .apply(
                                lambda x:
                                x.str.contains(
                                    busq_ventas,
                                    case=False,
                                    na=False
                                )
                            )
                            .any(axis=1)
                        ]
                    )

                else:

                    df_ventas_f = df_ventas

                st.dataframe(
                    df_ventas_f,
                    use_container_width=True,
                    height=300
                )

            except Exception as e:

                st.error(
                    f"Error en Ventas: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ======================================
    # NPS ADMIN
    # ======================================

    with col_nps:

        st.markdown(
            '<div class="panel-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="panel-title">
                ⭐ NPS (Satisfacción)
            </div>
            """,
            unsafe_allow_html=True
        )

        origen_nps = (
            "datos_nps.xlsx"
            if os.path.exists(
                "datos_nps.xlsx"
            )
            else None
        )

        if origen_nps is None:

            st.info(
                "⚠️ Sube "
                "'datos_nps.xlsx' "
                "en el panel lateral."
            )

        else:

            try:

                df_nps = pd.read_excel(
                    origen_nps,
                    sheet_name="NPS X asesor"
                )

                nps_pos_pct = (
                    calcular_porcentaje_nps_positivo(
                        df_nps
                    )
                )

                c_n_hex, st_n_lbl, _ = (
                    calcular_semaforo(
                        nps_pos_pct,
                        OBJETIVOS[
                            "nps_pct"
                        ]
                    )
                )

                n1, n2, n3 = st.columns(3)

                with n1:

                    st.markdown(
                        render_metric_html(
                            "Eval.",
                            f"{len(df_nps):,}",
                            "N/A",
                            "Activo",
                            "#3fb950"
                        ),
                        unsafe_allow_html=True
                    )

                with n2:

                    st.markdown(
                        render_metric_html(
                            "Positivo %",
                            f"{nps_pos_pct * 100:.1f}%",
                            f"{OBJETIVOS['nps_pct'] * 100:.0f}%",
                            st_n_lbl,
                            c_n_hex
                        ),
                        unsafe_allow_html=True
                    )

                with n3:

                    st.markdown(
                        render_metric_html(
                            "Promot.",
                            f"{int(
                                nps_pos_pct
                                *
                                len(df_nps)
                            )}",
                            "N/A",
                            "Óptimo",
                            "#3fb950"
                        ),
                        unsafe_allow_html=True
                    )

                st.markdown(
                    "<br>",
                    unsafe_allow_html=True
                )

                busq_nps = st.text_input(
                    "🔍 Buscar NPS:",
                    placeholder="Filtrar...",
                    key="b_nps_excel"
                )

                if busq_nps:

                    df_nps_f = (
                        df_nps[
                            df_nps
                            .astype(str)
                            .apply(
                                lambda x:
                                x.str.contains(
                                    busq_nps,
                                    case=False,
                                    na=False
                                )
                            )
                            .any(axis=1)
                        ]
                    )

                else:

                    df_nps_f = df_nps

                st.dataframe(
                    df_nps_f,
                    use_container_width=True,
                    height=300
                )

            except Exception as e:

                st.error(
                    f"Error en NPS: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ==========================================
    # CARRUSEL AUTOMÁTICO
    # ==========================================

    time.sleep(5)

    st.session_state[
        "carrusel_retencion"
    ] = (
        st.session_state[
            "carrusel_retencion"
        ] + 1
    ) % 3

    st.rerun()


# ==========================================
# 16. VISTA DEL ASESOR
# ==========================================

else:

    asesor_objetivo = (
        user_info["nombre_asesor"]
    )

    nombre_mostrar = (
        user_info["nombre_mostrar"]
    )

    st.markdown(
        f"""
        <div class="advisor-hero">

            <div>

                <span style="
                    background-color:
                        rgba(
                            16,
                            185,
                            129,
                            0.2
                        );

                    color:#3fb950;

                    padding:
                        4px 10px;

                    border-radius:6px;

                    font-size:11px;

                    font-weight:700;

                    border:
                        1px solid
                        rgba(
                            16,
                            185,
                            129,
                            0.4
                        );
                ">
                    🟢 ASESOR ACTIVO
                </span>

                <h2 style="
                    color:#f3f4f6;
                    margin:10px 0 5px 0;
                    font-weight:800;
                    letter-spacing:1px;
                ">
                    ¡Hola, {nombre_mostrar}! 👋
                </h2>

                <p style="
                    color:#9ca3af;
                    font-size:13px;
                    margin:0;
                ">
                    Panel de rendimiento personal
                    y seguimiento frente a los
                    objetivos individuales oficiales.
                </p>

            </div>

            <div style="
                text-align:right;
            ">

                <div style="
                    font-size:11px;
                    color:#9ca3af;
                    text-transform:uppercase;
                    font-weight:700;
                    letter-spacing:1px;
                ">
                    Meta de Ventas Asesor
                </div>

                <div style="
                    font-size:18px;
                    font-weight:800;
                    color:#fcd34d;
                    margin-top:4px;
                ">
                    🎯
                    {OBJETIVOS["ventas_individual"]}
                    Operaciones
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    col_asis_1, col_asis_2, col_asis_3 = st.columns(3)


    # ==========================================
    # MIS RETENCIONES
    # ==========================================

    with col_asis_1:

        st.markdown(
            """
            <div class="panel-box"
                 style="
                     border-top-color:#3fb950;
                 ">
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="panel-title">

                <span style="
                    color:#3fb950;
                ">
                    📌 Mis Retenciones
                </span>

                <span style="
                    font-size:11px;
                    color:#8b949e;
                ">
                    % Rete CTA / % Beneficio
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )

        origen_ret = (
            "datos_retenciones.xlsx"
            if os.path.exists(
                "datos_retenciones.xlsx"
            )
            else None
        )

        if origen_ret is None:

            st.info(
                "⚠️ Falta planilla "
                "de retenciones."
            )

        else:

            try:

                # ----------------------------------
                # RETES X ASESOR
                # ----------------------------------

                df_retes_asesor = (
                    cargar_hoja_excel(
                        origen_ret,
                        "Retes X Asesor"
                    )
                )

                df_mi_reg = (
                    filtrar_por_asesor_flexible(
                        df_retes_asesor,
                        asesor_objetivo
                    )
                )

                # ----------------------------------
                # MOSTRAR PORCENTAJES DEL ASESOR
                # ----------------------------------

                if (
                    df_mi_reg is not None
                    and
                    not df_mi_reg.empty
                ):

                    col_rete = (
                        buscar_columna_rete_cta(
                            df_mi_reg
                        )
                    )

                    col_beneficio = (
                        buscar_columna_beneficio(
                            df_mi_reg
                        )
                    )

                    mi_rete = None
                    mi_beneficio = None

                    if col_rete is not None:

                        mi_rete = (
                            normalizar_porcentaje(
                                df_mi_reg.iloc[0][
                                    col_rete
                                ]
                            )
                        )

                    if col_beneficio is not None:

                        mi_beneficio = (
                            normalizar_porcentaje(
                                df_mi_reg.iloc[0][
                                    col_beneficio
                                ]
                            )
                        )

                    if mi_rete is not None:

                        c_mi_rete, lbl_mi_rete, _ = (
                            calcular_semaforo(
                                mi_rete,
                                OBJETIVOS[
                                    "rete_pct"
                                ]
                            )
                        )

                    else:

                        c_mi_rete = "#8b949e"
                        lbl_mi_rete = "Sin datos"

                    if mi_beneficio is not None:

                        c_mi_beneficio, lbl_mi_beneficio, _ = (
                            calcular_semaforo(
                                mi_beneficio,
                                OBJETIVOS[
                                    "beneficio_pct"
                                ]
                            )
                        )

                    else:

                        c_mi_beneficio = "#8b949e"
                        lbl_mi_beneficio = "Sin datos"

                    r1, r2 = st.columns(2)

                    with r1:

                        st.markdown(
                            render_metric_html(
                                "% Rete CTA",
                                (
                                    f"{mi_rete * 100:.1f}%"
                                    if mi_rete is not None
                                    else "N/A"
                                ),
                                f"{OBJETIVOS['rete_pct'] * 100:.0f}%",
                                lbl_mi_rete,
                                c_mi_rete
                            ),
                            unsafe_allow_html=True
                        )

                    with r2:

                        st.markdown(
                            render_metric_html(
                                "% Beneficio",
                                (
                                    f"{mi_beneficio * 100:.1f}%"
                                    if mi_beneficio is not None
                                    else "N/A"
                                ),
                                f"{OBJETIVOS['beneficio_pct'] * 100:.0f}%",
                                lbl_mi_beneficio,
                                c_mi_beneficio
                            ),
                            unsafe_allow_html=True
                        )

                    st.markdown(
                        "<br>",
                        unsafe_allow_html=True
                    )

                    # Formatear tabla
                    df_mi_mostrar = (
                        df_mi_reg.copy()
                    )

                    for col in df_mi_mostrar.columns:

                        nombre_col = (
                            str(col).lower()
                        )

                        if (
                            "%"
                            in str(col)
                            or
                            "rete"
                            in nombre_col
                            or
                            "benef"
                            in nombre_col
                            or
                            "pct"
                            in nombre_col
                            or
                            "porcentaje"
                            in nombre_col
                        ):

                            df_mi_mostrar[col] = (
                                df_mi_mostrar[col]
                                .apply(
                                    lambda x:
                                    formatear_porcentaje(x)
                                    if pd.notnull(x)
                                    else x
                                )
                            )

                    st.dataframe(
                        df_mi_mostrar,
                        use_container_width=True,
                        height=250
                    )

                else:

                    st.warning(
                        "Sin registros activos "
                        "en Retes X Asesor."
                    )

            except Exception as e:

                st.error(
                    f"Error en retenciones: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ==========================================
    # MIS VENTAS
    # ==========================================

    with col_asis_2:

        st.markdown(
            """
            <div class="panel-box"
                 style="
                     border-top-color:#3b82f6;
                 ">
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="panel-title">

                <span style="
                    color:#3b82f6;
                ">
                    💰 Mis Ventas
                </span>

                <span style="
                    font-size:11px;
                    color:#8b949e;
                ">
                    Meta Ind.:
                    {OBJETIVOS["ventas_individual"]}
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )

        origen_ven = (
            "datos_ventas.xlsx"
            if os.path.exists(
                "datos_ventas.xlsx"
            )
            else None
        )

        if origen_ven is None:

            st.info(
                "⚠️ Falta planilla "
                "de ventas."
            )

        else:

            try:

                df_ventas_full = (
                    pd.read_excel(
                        origen_ven,
                        sheet_name="Ventas X asesor"
                    )
                )

                df_mi_ven = (
                    filtrar_por_asesor_flexible(
                        df_ventas_full,
                        asesor_objetivo
                    )
                )

                if not df_mi_ven.empty:

                    st.dataframe(
                        df_mi_ven,
                        use_container_width=True,
                        height=250
                    )

                else:

                    st.warning(
                        "Sin registros activos "
                        "en ventas."
                    )

            except Exception as e:

                st.error(
                    f"Error: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ==========================================
    # MIS NPS
    # ==========================================

    with col_asis_3:

        st.markdown(
            """
            <div class="panel-box"
                 style="
                     border-top-color:#f59e0b;
                 ">
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="panel-title">

                <span style="
                    color:#f59e0b;
                ">
                    ⭐ Mis Evaluaciones NPS
                </span>

                <span style="
                    font-size:11px;
                    color:#8b949e;
                ">
                    Meta Positiva:
                    {OBJETIVOS["nps_pct"] * 100:.0f}%
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )

        origen_nps = (
            "datos_nps.xlsx"
            if os.path.exists(
                "datos_nps.xlsx"
            )
            else None
        )

        if origen_nps is None:

            st.info(
                "⚠️ Falta planilla "
                "de NPS."
            )

        else:

            try:

                df_nps_full = (
                    pd.read_excel(
                        origen_nps,
                        sheet_name="NPS X asesor"
                    )
                )

                df_mi_nps = (
                    filtrar_por_asesor_flexible(
                        df_nps_full,
                        asesor_objetivo
                    )
                )

                if (
                    not df_nps_full.empty
                    and
                    not df_mi_nps.empty
                ):

                    nps_mi_pos = (
                        calcular_porcentaje_nps_positivo(
                            df_mi_nps
                        )
                    )

                    c_n_mi, lbl_n_mi, _ = (
                        calcular_semaforo(
                            nps_mi_pos,
                            OBJETIVOS[
                                "nps_pct"
                            ]
                        )
                    )

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#0d1117;
                            padding:8px;
                            border-radius:6px;
                            margin-bottom:8px;
                            text-align:center;
                            font-size:13px;
                            font-weight:bold;
                            color:{c_n_mi};
                        ">
                            📊 Tu NPS Positivo Personal:
                            {nps_mi_pos * 100:.1f}%
                            <br>

                            <span style="
                                font-size:11px;
                            ">
                                ● {lbl_n_mi}
                            </span>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.dataframe(
                        df_mi_nps,
                        use_container_width=True,
                        height=200
                    )

                else:

                    st.warning(
                        "Sin registros activos "
                        "en NPS."
                    )

            except Exception as e:

                st.error(
                    f"Error procesando NPS: {e}"
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )
