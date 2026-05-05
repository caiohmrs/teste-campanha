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
                    st.caption(f"- **Função:** `{erro.get('funcao', 'N/A')}`\n- **Tipo:** `{erro.get('tipo', 'N/A')}`\n- **Data:** {erro.get('data', 'N/A')}")
                with col_info2:
                    st.markdown("**🔍 MENSAGEM:**")
                    st.error(erro.get('erro', 'Sem mensagem'))
                if erro.get('traceback', ''):
                    st.markdown("**📜 TRACEBACK COMPLETO:**")
                    st.code(erro.get('traceback', ''), language="python")
                st.markdown("<br>", unsafe_allow_html=True)
                col_copy, col_clear = st.columns(2)
                with col_copy:
                    st.code(f"{erro.get('tipo', '')}: {erro.get('erro', '')}", language="python")
                with col_clear:
                    if st.button("🗑️ Remover este erro", key=f"del_err_{i}"):
                        st.session_state['error_log'].remove(erro)
                        st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        col_acoes = st.columns(3)
        with col_acoes[0]:
            if st.button("🗑️ LIMPAR TODOS OS ERROS", width='stretch', type="primary"):
                st.session_state['error_log'] = []
                st.rerun()
        with col_acoes[1]:
            if st.button("📥 BAIXAR LOG (JSON)", width='stretch'):
                json_str = json.dumps(erros, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"erros_{get_agora_br().strftime('%Y%m%d_%H%M%S')}.json",
                    mime='application/json',
                    width='stretch'
                )
        with col_acoes[2]:
            if st.button("📋 COPIAR ÚLTIMO ERRO", width='stretch'):
                if erros:
                    st.code(erros[-1].get('traceback', ''), language="python")

# ------------------------------------------------------------------
# Aba Ações
# ------------------------------------------------------------------
with tab_acoes:
    st.markdown("### 👁️ MONITORAMENTO DE AÇÕES EM TEMPO REAL")
    c_f1, c_f2, c_f3 = st.columns(3)
    if df_logs is not None and not df_logs.empty:
        datas_disponiveis = sorted(
            [d for d in df_logs['Data_Hora'].str.split().str[0].unique().tolist() if "/" in str(d)],
            reverse=True
        )
        data_filtro = st.selectbox("📅 DATA:", ["Todas"] + datas_disponiveis)
        tipos_acao = df_logs['Tipo_Acao'].unique().tolist()
        tipo_filtro = st.selectbox("🎯 TIPO DE AÇÃO:", ["Todos"] + tipos_acao)
        if data_filtro != "Todas":
            df_logs = df_logs[df_logs['Data_Hora'].str.contains(data_filtro)]
        if tipo_filtro != "Todos":
            df_logs = df_logs[df_logs['Tipo_Acao'].str.contains(tipo_filtro)]
        if not df_logs.empty:
            st.dataframe(df_logs.sort_values('Data_Hora', ascending=False)[
                ['Data_Hora', 'ID_Usuario', 'Tipo_Acao', 'Localização', 'Feedback']
            ], hide_index=True, width='stretch')
    else:
        st.warning("⚠️ NENHUM DADO DE LOG ENCONTRADO")

# ------------------------------------------------------------------
# Aba Simulador
# ------------------------------------------------------------------
with tab_simulador:
    st.markdown("### 🧪 SIMULADOR DE AÇÕES (TESTE)")
    st.info("💡 Use esta ferramenta para testar funcionalidades sem afetar dados reais")
    sim_id = st.text_input("ID DO USUÁRIO (para teste):", value=u['ID_Usuario'])
    sim_acao = st.selectbox("TIPO DE AÇÃO:", [
        "Check-in", "Check-out", "CONCLUIU: MISSÃO", "AÇÃO: INTERAÇÃO INSTAGRAM", "AÇÃO: MOBILIZAÇÃO WHATSAPP"
    ])
    if st.button("🧪 EXECUTAR SIMULAÇÃO", width='stretch', type="primary"):
        resultado = simular_acao_usuario(sim_id, sim_acao, st.secrets, st.session_state.get('error_log'))
        st.json(resultado)

# ------------------------------------------------------------------
# Aba Sistema
# ------------------------------------------------------------------
with tab_sistema:
    st.markdown("### ⚙️ INFORMAÇÕES DO SISTEMA")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<b>Pacotes instalados</b>")
        for pkg in ['streamlit', 'pandas', 'gspread', 'google-auth', 'geopy', 'folium']:
            try:
                ver = __import__(pkg.replace('-', '_')).__version__
                st.markdown(f"`{pkg}`: **{ver}**")
            except Exception:
                st.markdown(f"`{pkg}`: *não encontrado*")
    with c2:
        st.markdown("<b>Estatísticas de uso</b>")
        api_info = contar_chamadas_api()
        for k, v in api_info.items():
            st.markdown(f"**{k}:** {v}")
        st.markdown(f"**Horário do Servidor:** {get_agora_br().strftime('%d/%m/%Y %H:%M:%S')}")
    if st.button("🔄 LIMPAR TODO O CACHE", width='stretch'):
        st.cache_data.clear()
        st.success("✅ Cache limpo! A página será recarregada.")
        time.sleep(2)
        st.rerun()
