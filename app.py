import os
import streamlit as st

# Configuración inicial de la página (Ancho completo para el Wallboard)
st.set_page_config(
    page_title="Proyecto Cardinal — Consola de Supervisión",
    page_icon="🧭",
    layout="wide",
)

# Inyección de Estilos CSS Globales
st.markdown(
    """
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 0.95rem;
        color: #8b949e;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        margin: 8px 0;
    }
    .sem-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .sem-verde { background-color: rgba(63, 185, 80, 0.2); color: #3fb950; border: 1px solid #3fb950; }
    .sem-amarillo { background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .sem-rojo { background-color: rgba(248, 81, 73, 0.2); color: #f85149; border: 1px solid #f85149; }
    .sem-gris { background-color: rgba(139, 148, 158, 0.2); color: #8b949e; border: 1px solid #8b949e; }
    </style>
""",
    unsafe_allow_html=True,
)

# Importaciones de los módulos principales del panel y asistencias
import asistencias
from dashboard import mostrar_panel_admin, mostrar_panel_asesor

# Intentar cargar objetivos desde config
try:
  from config import cargar_objetivos
except ImportError:

  def cargar_objetivos():
    return {
        "rete_pct": 0.70,
        "beneficio_pct": 0.40,
        "nps_pct": 0.65,
        "ventas_grupal": 260,
    }


# --- AUTENTICACIÓN SEGURA CONECTADA A CONFIG.PY (MODIFICADA CON st.form PARA ENTER) ---
from config import USUARIOS_PERFILES


def autenticar_usuario():
  if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

  if not st.session_state["autenticado"]:
    st.markdown(
        "<h2 style='text-align: center; color: #58a6ff;'>🔐 Proyecto Cardinal"
        " — Ingreso</h2>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
      # st.form permite disparar el login al presionar Enter en cualquier input
      with st.form(key="login_form"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        submit_login = st.form_submit_button(
            "Iniciar Sesión", type="primary", use_container_width=True
        )

        if submit_login:
          user_key = u.strip().lower()
          if (
              user_key in USUARIOS_PERFILES
              and USUARIOS_PERFILES[user_key]["password"] == p
          ):
            datos = USUARIOS_PERFILES[user_key]
            st.session_state["autenticado"] = True
            st.session_state["user"] = user_key
            st.session_state["rol"] = datos.get("rol", "Asesor")
            st.session_state["nombre_mostrar"] = datos.get("nombre_mostrar", u)
            st.session_state["asesor_objetivo"] = datos.get(
                "nombre_asesor", None
            )
            st.rerun()
          else:
            st.error("Usuario o contraseña incorrectos.")
    return None, None, None, None
  else:
    return (
        st.session_state["user"],
        st.session_state["rol"],
        st.session_state["nombre_mostrar"],
        st.session_state["asesor_objetivo"],
    )


# --- RETENCIONES / ESTADOS SEGURO ---
inicializar_estado_archivos = lambda: None
try:
  import retenciones

  if hasattr(retenciones, "inicializar_estado_archivos"):
    inicializar_estado_archivos = retenciones.inicializar_estado_archivos
except ImportError:
  pass

# Inicializar estados de archivos y objetivos
inicializar_estado_archivos()
if "objetivos" not in st.session_state:
  st.session_state["objetivos"] = cargar_objetivos()

# --- DETECCIÓN DE MODO PROYECCIÓN (URL QUERY PARAMS) ---
query_params = st.query_params
modo_proyeccion = query_params.get("view") == "wallboard"

if modo_proyeccion:
  from wallboard import mostrar_wallboard_proyeccion

  origen_ret = st.session_state.get("origen_retenciones", None)
  origen_nps = st.session_state.get("origen_nps", None)
  origen_ventas = st.session_state.get("origen_ventas", None)
  objetivos = st.session_state["objetivos"]

  mostrar_wallboard_proyeccion(origen_ret, origen_nps, origen_ventas, objetivos)
else:
  # FLUJO NORMAL CON LOGIN OBLIGATORIO
  usuario, rol, nombre_mostrar, asesor_objetivo = autenticar_usuario()

  if not usuario:
    st.stop()

  # -------------------------------------------------------------
  # BARRA SUPERIOR: BOTÓN PROYECTAR A LA DERECHA (Solo Admin/Master/Supervisor)
  # -------------------------------------------------------------
  if rol in ["Master", "Administrador", "Supervisor"]:
    col_top_l, col_top_r = st.columns([6, 1])
    with col_top_r:
      st.markdown(
          """
            <div style="text-align: right; padding-top: 5px;">
                <a href="?view=wallboard" target="_blank" style="
                    background-color: #238636;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 14px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    display: inline-block;
                ">PROYECTAR 🖥️</a>
            </div>
            """,
          unsafe_allow_html=True,
      )

  # Panel Lateral (Sidebar)
  st.sidebar.markdown(f"### 🧭 Panel de Control")
  st.sidebar.markdown(f"**Usuario:** {nombre_mostrar}")
  st.sidebar.markdown(f"**Rol:** {rol}")
  st.sidebar.markdown("---")

  if rol in ["Master", "Administrador", "Supervisor"]:
    opciones_menu = ["Métricas y Supervisión"]

    # Agregamos la sección de Gestión de Asistencias para supervisores y admins
    opciones_menu.append("Gestión de Asistencias")

    if rol in ["Master", "Administrador"]:
      opciones_menu.append("Gestión de Objetivos")

    seleccion = st.sidebar.radio("Secciones", opciones_menu)

    # Carga de planillas lateral exclusiva para Supervisores/Admin
    st.sidebar.markdown("### 📂 Gestión de Archivos")
    origen_retenciones = st.sidebar.file_uploader(
        "Actualizar Retenciones (.xlsx)", type=["xlsx"], key="up_ret"
    )
    origen_nps = st.sidebar.file_uploader(
        "Actualizar NPS (.xlsx)", type=["xlsx"], key="up_nps"
    )
    origen_ventas = st.sidebar.file_uploader(
        "Actualizar Ventas (.xlsx)", type=["xlsx"], key="up_ven"
    )

    # --- PERSISTENCIA AUTOMÁTICA EN DISCO ---
    if origen_retenciones is not None:
      with open("datos_retenciones.xlsx", "wb") as f:
        f.write(origen_retenciones.getbuffer())

    if origen_nps is not None:
      with open("datos_nps.xlsx", "wb") as f:
        f.write(origen_nps.getbuffer())

    if origen_ventas is not None:
      with open("datos_ventas.xlsx", "wb") as f:
        f.write(origen_ventas.getbuffer())

    # Guardar en sesión para el Wallboard
    st.session_state["origen_retenciones"] = origen_retenciones
    st.session_state["origen_nps"] = origen_nps
    st.session_state["origen_ventas"] = origen_ventas
  else:
    # Los asesores NO ven opciones de configuración ni subida de archivos
    seleccion = "Métricas y Supervisión"
    origen_retenciones = None
    origen_nps = None
    origen_ventas = None

  st.sidebar.markdown("---")
  if st.sidebar.button("Cerrar Sesión", type="secondary"):
    st.session_state["autenticado"] = False
    st.session_state.pop("user", None)
    st.rerun()

  # Cuerpo Principal (Enrutamiento)
  if seleccion == "Métricas y Supervisión":
    if rol in ["Master", "Administrador", "Supervisor"]:
      mostrar_panel_admin(
          origen_retenciones,
          origen_nps,
          origen_ventas,
          st.session_state["objetivos"],
          rol,
      )
    else:
      mostrar_panel_asesor(
          nombre_mostrar,
          asesor_objetivo,
          origen_retenciones,
          origen_nps,
          origen_ventas,
          st.session_state["objetivos"],
      )

  elif seleccion == "Gestión de Asistencias":
    # Llamada al nuevo módulo exclusivo de asistencias
    asistencias.mostrar_gestion_asistencias()

  elif seleccion == "Gestión de Objetivos":
    if rol in ["Master", "Administrador"]:
      st.subheader("⚙️ Gestión y Configuración de Objetivos")
      objs = st.session_state["objetivos"]

      col1, col2 = st.columns(2)
      with col1:
        new_rete = (
            st.number_input(
                "Meta % Rete CTA",
                value=float(objs.get("rete_pct", 0.70) * 100),
                step=1.0,
            )
            / 100.0
        )
        new_bene = (
            st.number_input(
                "Meta % Beneficio",
                value=float(objs.get("beneficio_pct", 0.40) * 100),
                step=1.0,
            )
            / 100.0
        )
      with col2:
        new_nps = (
            st.number_input(
                "Meta % NPS Positivo",
                value=float(objs.get("nps_pct", 0.65) * 100),
                step=1.0,
            )
            / 100.0
        )
        new_ventas = int(
            st.number_input(
                "Meta Ventas Grupales",
                value=int(objs.get("ventas_grupal", 260)),
                step=5,
            )
        )

      if st.button("Guardar Objetivos", type="primary"):
        st.session_state["objetivos"] = {
            "rete_pct": new_rete,
            "beneficio_pct": new_bene,
            "nps_pct": new_nps,
            "ventas_grupal": new_ventas,
        }
        st.success("¡Objetivos actualizados correctamente!")
    else:
      st.error("No tienes permisos para acceder a esta sección.")