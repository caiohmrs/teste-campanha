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

# ---------- INICIALIZAÇÃO DE VARIÁVEL DE SESSÃO ----------
if "mensagem_exibida" not in st.session_state:
    st.session_state["mensagem_exibida"] = False
# -----------------------------------------------------
# ----------------------------------------------------------------------
# 1️⃣  Garantir que a sessão tenha a chave "usuario_logado"
# ----------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# ----------------------------------------------------------------------
# 2️⃣  Se não houver usuário logado, enviar para a tela de login
# ----------------------------------------------------------------------
if st.session_state["usuario_logado"] is None:
    # limpa possíveis caches que já foram criados antes do redirect
    st.cache_data.clear()
    st.switch_page("pages/00_Login.py")
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
        st.session_state.pop("google_credentials", None)

        try:
            cookie_manager.delete("comando2026_user_id", key="del_user")
            cookie_manager.delete("comando2026_checkin_time", key="del_check")
        except KeyError:
            pass
        except Exception as e:
            st.session_state['error_log'].append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'sidebar.logout',
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

# ------------------------------------------------------------------
# Aba Diagnóstico
# ------------------------------------------------------------------
with tab_diagnostico:
    st.markdown("### 🔍 TESTE DE CONEXÕES")
    if st.button("🔄 EXECUTAR RECURSO REPRODUÇÃO", type="primary", width='stretch'):
        with st.spinner("Testando todas as conexões..."):
            diagnostico = diagnosticar_conexoes(st.secrets, st.session_state.get('error_log'))
            st.markdown("<br>", unsafe_allow_html=True)

            # Exibir cartões de diagnóstico
            cols = st.columns(4)
            for col, (nome, dado) in zip(cols, diagnostico.items()):
                render_diagnostic_card(
                    titulo=nome.upper(),
                    status=dado["status"],
                    mensagem=dado["msg"],
                    cor_fundo="#00FF00" if dado["status"] == "✅" else "#FF0000"
                )
            # Detalhes avançados
            with st.expander("📋 DETALHES TÉCNICOS", expanded=True):
                st.json(diagnostico)

# ------------------------------------------------------------------
# Aba Logs de Erro
# ------------------------------------------------------------------
with tab_logs_erro:
    st.markdown("### 📛 LOGS DE ERRO (SESSÃO ATUAL)")
    erros = obter_logs_erros(st.session_state.get('error_log', []), limite=100)

    c_err1, c_err2, c_err3, c_err4 = st.columns(4)
    total_erros = len(erros)
    erros_criticos = len([e for e in erros if 'CRITICAL' in e.get('tipo', '').upper() or 'KeyError' in e.get('tipo', '')])
    # Correção da expressão de compreensão: usar 'e in erros' corretamente
    erros_funcoes = len(set([e.get('funcao', '') for e in erros]))
    ultimo_erro = erros[-1].get('data', 'N/A') if erros else 'Nenhum'

    c_err1.metric("📛 Total Erros", total_erros)
    c_err2.metric("⚠️ Críticos", erros_criticos, delta_color="inverse")
    c_err3.metric("🔧 Funções Afetadas", erros_funcoes)
    c_err4.metric("🕒 Último Erro", ultimo_erro.split(' ')[-1] if ultimo_erro != 'Nenhum' else 'N/A')
    st.markdown("<br>", unsafe_allow_html=True)

    if not erros:
        st.success("✅ NENHUM ERRO REGISTRADO NESTA SESSÃO")
    else:
        st.warning(f"⚠️ {len(erros)} ERRO(S) ENCONTRADO(S)")
        tipos_erro = list(set([e.get('tipo', 'Desconhecido') for e in erros]))
        filtro_tipo = st.selectbox("🔍 FILTRAR POR TIPO:", ["Todos"] + tipos_erro)
        erros_filtrados = erros if filtro_tipo == "Todos" else [e for e in erros if e.get('tipo', '') == filtro_tipo]
        for i, erro in enumerate(erros_filtrados[::-1]):
            cor_borda = "#FF0000" if "KeyError" in erro.get('tipo', '') or "Critical" in erro.get('tipo', '') else "var(--cor-secundaria)"
            with st.expander(f"❌ ERRO #{len(erros_filtrados)-i} | {erro.get('tipo', 'N/A')} | {erro.get('data', 'N/A')}"):
                col_info1, col_info2 = st.columns([1, 3])
                with col_info1:
                    st.markdown("**📋 INFO:**")
                    ...

# Nota: As demais abas (tab_acoes, tab_simulador, tab_sistema) permanecem inalteradas.
