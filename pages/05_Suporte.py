# =============================================================================
# PAGES/05_🔧_SUPORTE.PY – VISÃO SUPORTE (bloco anteriormente em 01_Principal.py)
# =============================================================================

import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from streamlit_js_eval import get_geolocation
import time
import traceback
from datetime import datetime
import json

from funcoes import (
    get_agora_br,
    diagnosticar_conexoes,
    obter_logs_erros,
    contar_chamadas_api,
    simular_acao_usuario,
    carregar_dados
)

from utils.styles import inject_styles
from utils.components import (
    render_support_panel,
    render_diagnostic_card,
    render_log_entry,
    render_metric_card,
    render_metric_row
)

# CONFIGURAÇÃO INICIAL
st.set_page_config(
    page_title="COMANDO 2026 – Suporte",
    page_icon="🛠️",
    layout="wide"
)

inject_styles()

# INICIALIZAR COOKIE MANAGER
cookie_manager = stx.CookieManager()

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# CAPTURA DE VARIÁVEL DO USUÁRIO
u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()

# SIDEBAR (mesma lógica de logout)
with st.sidebar:
    st.header("👤 Perfil")
    st.write(f"Olá, **{u['Nome'].split()[0]}**")
    st.caption(f"Cargo: {u['Cargo']}")

    if st.button("🔄 ATUALIZAR PAINEL", width="stretch"):
        with st.spinner("Atualizando..."):
            st.cache_data.clear()
            st.rerun()

    if st.button("Sair / Trocar Conta", width='stretch'):
        st.session_state["logout_em_andamento"] = True
        st.session_state["usuario_logado"] = None
        st.session_state["mensagem_exibida"] = False

        try:
            cookie_manager.delete("comando2026_user_id", key="del_user")
            cookie_manager.delete("comando2026_checkin_time", key="del_check")
        except KeyError:
            pass
        except Exception as e:
            st.session_state['error_log'].append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'logout',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })

        st.success("Saindo e limpando dados")
        st.session_state.clear()
        st.cache_data.clear()
        time.sleep(1)
        st.switch_page("pages/00_Login.py")

# CABEÇALHO
render_support_panel()

df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))

tab_diagnostico, tab_logs_erro, tab_acoes, tab_simulador, tab_sistema = st.tabs([
    "🔍 DIAGNÓSTICO", "📛 LOGS DE ERRO", "👁️ TODAS AS AÇÕES", "🧪 SIMULADOR", "⚙️ SISTEMA"
])

with tab_diagnostico:
    st.markdown("### 🔍 TESTE DE CONEXÕES")
    if st.button("🔄 EXECUTAR RECURSO REPRODUÇÃO   “  ​ “”   ” &quot </</</</