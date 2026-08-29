import time
import streamlit as st
from config import USUARIOS_PERFILES


def mostrar_login():
  """Maneja la autenticación de usuarios en el sistema Cardinal.

  Valida credenciales usando el diccionario centralizado de config.py,
  actualiza el st.session_state y detiene la ejecución si el usuario no ha
  iniciado sesión.
  """
  # Asegurar variables de estado iniciales
  if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
  if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
  if "rol_actual" not in st.session_state:
    st.session_state["rol_actual"] = None

  # Si ya está autenticado, no muestra el login
  if st.session_state["autenticado"]:
    return

  # Renderizado de títulos institucionales
  st.markdown(
      "<div style='text-align: center; font-size: 2.5rem; font-weight: 800;"
      " color: #58a6ff; margin-bottom: 0px;'>CARDINAL</div>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<div style='text-align: center; font-size: 1.1rem; color: #8b949e;"
      " margin-bottom: 25px;'>Torre de Control Operativa</div>",
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 1.2, 1])
  with col2:
    st.markdown(
        "<div style='background-color: #161b22; padding: 30px; border-radius:"
        " 12px; border: 1px solid #30363d;'>",
        unsafe_allow_html=True,
    )
    st.subheader("🔐 Inicio de Sesión")

    usuario_input = st.text_input("Usuario", key="input_usuario_login")
    password_input = st.text_input(
        "Contraseña", type="password", key="input_pass_login"
    )

    if st.button("Ingresar al Sistema", key="btn_submit_login"):
      user_key = usuario_input.strip().lower()
      if (
          user_key in USUARIOS_PERFILES
          and USUARIOS_PERFILES[user_key]["password"] == password_input
      ):
        st.session_state["autenticado"] = True
        st.session_state["usuario_actual"] = user_key
        st.session_state["rol_actual"] = USUARIOS_PERFILES[user_key]["rol"]
        st.success("¡Acceso concedido!")
        time.sleep(0.5)
        st.rerun()
      else:
        st.error("Usuario o contraseña incorrectos.")

    st.markdown("</div>", unsafe_allow_html=True)

  # Detiene la ejecución del script principal hasta que se autentique con éxito
  st.stop()