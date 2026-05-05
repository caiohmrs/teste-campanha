# =============================================================================
# PAGES/01_🚀_PRINCIPAL.PY – ROTEADOR CENTRAL
# =============================================================================

import streamlit as st
import extra_streamlit_components as stx
import traceback
import sys
from datetime import datetime
import time

from funcoes import get_agora_br, contar_chamadas_api
from utils.styles import inject_styles

# CONFIGURAÇÃO INICIAL
st.set_page_config(
    page_title="COMANDO 2026 – Router",
    page_icon="🧭",
    layout="wide"
)

inject_styles()

# =============================================================================
# VERIFICAR AUTENTICAÇÃO (mantém o mesmo código que já existia)
# =============================================================================

cookie_manager = stx.CookieManager()

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "logout_em_andamento" not in st.session_state:
    st.session_state["logout_em_andamento"] = False

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# Redirecionar se não logado
if st.session_state["usuario_logado"] is None:
    st.switch_page("pages/00_Login.py")

# =============================================================================
# CAPTURA DO USUÁRIO LOGADO
# =============================================================================

u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora = get_agora_br()

# =============================================================================
# ROTEAMENTO POR CARGO
# =============================================================================

if cargo_limpo == "colaborador":
    st.switch_page("pages/02_Colaborador.py")
elif cargo_limpo == "supervisor":
    st.switch_page("pages/03_Supervisor.py")
elif cargo_limpo == "admin":
    st.switch_page("pages/04_Admin.py")
elif cargo_limpo == "suporte":
    st.switch_page("pages/05_Suporte.py")
else:
    st.error("❌ CARGO desconhecido")
    st.stop()

# =============================================================================
# CAPTURA DE ERROS GLOBAL (mantém a função já existente)
# =============================================================================
def inicializar_captura_erros():
    def excecao_global(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        erro_info = {
            'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'erro': str(exc_value),
            'funcao': 'GLOBAL_UNCAUGHT',
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            'tipo': exc_type.__name__
        }

        st.session_state['error_log'].append(erro_info)
        print(f"🚨 ERRO GLOBAL CAPTURADO: {erro_info['tipo']} - {erro_info['erro']}")

    sys.excepthook = excecao_global

inicializar_captura_erros()
