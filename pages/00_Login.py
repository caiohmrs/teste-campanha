# =============================================================================
# PAGES/00_LOGIN.PY - TELA DE LOGIN COM GOOGLE OAUTH
# =============================================================================

import streamlit as st

from utils.styles import inject_styles
from utils.components import render_login_header, render_login_box
from utils.auth import login_google

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================

st.set_page_config(
    page_title="Max Maciel 2026 - Login",
    page_icon="",
    layout="centered"
)

inject_styles()

# =============================================================================
# INICIALIZAR ESTADO
# =============================================================================

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# =============================================================================
# MOSTRAR ERRO DO OAUTH (se veio do campanha.py)
# =============================================================================

oauth_error = st.session_state.pop("_oauth_error", None)
if oauth_error:
    st.error(oauth_error)

# =============================================================================
# REDIRECIONAR SE JA LOGADO
# =============================================================================

if st.session_state.get("usuario_logado") is not None:
    st.switch_page("pages/01_Principal.py")

# =============================================================================
# TELA DE LOGIN
# =============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])

with col_l2:
    render_login_header()

    with st.container():
        render_login_box()

        # Botao de login Google (botao HTML customizado estilo oficial)
        login_google()
