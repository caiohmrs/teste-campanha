# =============================================================================
# PAGES/04_🔐_ADMIN.PY – VISÃO ADMIN (bloco anteriormente em 01_Principal.py)
# =============================================================================

import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from streamlit_js_eval import get_geolocation
import time
import urllib.parse
import xlsxwriter
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta, timezone
import io
import sys
import traceback
import json

from funcoes import (
    get_agora_br,
    validar_gps_basico,
    sanitize_whatsapp,
    obter_endereco_simples,
    _get_gspread_client,
    _get_drive_credentials,
    carregar_dados,
    salvar_foto_drive,
    salvar_documento_drive,
    registrar_acao,
    registrar_novo_contrato_admin,
    atualizar_contrato_enviado,
    carregar_macro_grupos_cached,
    carregar_grupos_completos_cached,
    criar_novo_grupo,
    criar_novo_macro_grupo,
    diagnosticar_conexoes,
    obter_logs_erros,
    contar_chamadas_api,
    simular_acao_usuario
)

from utils.styles import inject_styles
from utils.components import (
    render_welcome_banner,
    render_status_bar,
    render_section_header,
    render_modal_header,
    render_info_banner,
    render_ticker,
    render_team_card,
    render_metric_card,
    render_support_panel,
    render_diagnostic_card,
    render_log_entry,
    render_contract_entry,
    render_action_link_button,
    render_metric_row,
)

# CONFIGURAÇÃO INICIAL
st.set_page_config(
    page_title="COMANDO 2026 – Admin",
    page_icon="🛠️",
    layout="wide"
)

inject_styles()

# INICIALIZAR COOKIE MANAGER
cookie_manager = stx.CookieManager()

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# CAPTURA DE VARIÁVEIS DO USUÁRIO
u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora_br = get_agora_br()
hoje_str = agora_br.strftime("%d/%m/%Y")

# SIDEBAR (logout etc.)
with st.sidebar:
    st.header("👤 Perfil")
    st.write(f"Olá, **{u['Nome'].split()[0]}**")
    st.caption(f"Cargo: {u['Cargo']}")

    if st.button("🔄 ATUALIZAR PAINEL", width="stretch"):
        with st.spinner("Buscando dados..."):
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
                'funcao': 'sidebar.logout',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })

        st.success("Saindo e limpando dados...")
        st.session_state.clear()
        st.cache_data.clear()
        time.sleep(2)
        st.switch_page("pages/00_Login.py")

# CABEÇALHO BEM-VINDO (pode ser omitido ou mantido)
render_welcome_banner(u['Nome'])

# ======================================================================
# ABAS ADMINISTRATIVAS
# ======================================================================
tab_hierarquia, tab_logs, tab_mapa, tab_mensagens, tab_cadastro, tab_contratos = st.tabs([
    "👥 EQUIPES", "📊 DASHBOARD", "🗺️ MAPA", "📝 MISSÕES", "➕ CADASTRO", "📄 CONTRATOS"
])

# ------------------------------------------------------------------
# ABA 1: ESTRUTURA DE EQUIPES (MACRO_GRUPOS DINÂMICOS)
# ------------------------------------------------------------------
with tab_hierarquia:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>ESTRUTURA DE EQUIPES</h2>",
        unsafe_allow_html=True)

    planilha_id = st.secrets["planilha"]["id"]
    macro_grupos_disponiveis = carregar_macro_grupos_cached(planilha_id)

    st.markdown(
        "<p style='font-family: \"Archivo Black\", sans-serif; font-size: 0.9rem; margin-bottom: 5px;'>📍 SELECIONE A MACRO REGIÃO:</p>",
        unsafe_allow_html=True)

    macro_selecionada = st.selectbox(
        "FILTRO_MACRO",
        ["TODAS AS REGIÕES"] + macro_grupos_disponiveis,
        label_visibility="collapsed",
        key="select_macro_hierarquia"
    )

    df_usuarios_raw = carregar_dados("Usuarios", planilha_id, st.session_state.get('error_log'))
    df_grupos_info = carregar_dados("Grupos", planilha_id, st.session_state.get('error_log'))
    # Carrega logs para cálculo de supervisores ativos hoje
    df_logs = carregar_dados("Logs", planilha_id, st.session_state.get('error_log'))

    if df_usuarios_raw is not None and df_grupos_info is not None:
        df_gerencial = pd.merge(df_usuarios_raw, df_grupos_info, on='ID_Grupo', how='left')
        df_gerencial['Macro_Grupo'] = df_gerencial['Macro_Grupo'].fillna("GERAL")

        if macro_selecionada == "TODAS AS REGIÕES":
            df_f_admin = df_gerencial.copy()
        else:
            df_f_admin = df_gerencial[df_gerencial['Macro_Grupo'] == macro_selecionada]

        supervisores = df_f_admin[df_f_admin['Cargo'].str.lower().str.strip() == "supervisor"]

        if supervisores.empty:
            st.warning("Nenhum supervisor nesta região.")
        else:
            col_sup1, col_sup2 = st.columns(2, gap="large")
            for i, (_, sup) in enumerate(supervisores.iterrows()):
                col_alvo = col_sup1 if i % 2 == 0 else col_sup2
                with col_alvo:
                    equipe = df_f_admin[df_f_admin['ID_Supervisor'].astype(str).str.strip() == str(sup['ID_Usuario']).strip()]
                    qtd_equipe = len(equipe)
                    # Correção: garantir que df_logs esteja definido
                    logs_eq = df_logs[(df_logs['ID_Usuario'].isin(equipe['ID_Usuario'])) &
                                      (df_logs['Data_Hora'].str.contains(hoje_str))]
                    ativos_hoje = logs_eq[logs_eq['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
                    render_team_card(
                        supervisor=sup['Nome'],
                        macro_grupo=sup['Macro_Grupo'],
                        id_grupo=sup['ID_Grupo'],
                        qtd_equipe=qtd_equipe,
                        ativos_hoje=ativos_hoje
                    )
                    w_sup_limpo = sanitize_whatsapp(str(sup.get('WhatsApp', '')).strip())
                    link_grp = str(sup.get('Link_Grupo', '')).strip()
                    c_wa1, c_wa2 = st.columns(2)
                    with c_wa1:
                        if w_sup_limpo:
                            st.link_button(f"👤 CHAT: {sup['Nome'].split()[0].upper()}",
                                           f"https://wa.me/{w_sup_limpo}", width="stretch")
                        else:
                            st.button("👤 SEM WHATSAPP", disabled=True, width="stretch",
                                      key=f"no_wa_{sup['ID_Usuario']}")
                    with c_wa2:
                        if link_grp and "chat.whatsapp" in link_grp:
                            st.link_button("📢 GRUPO", f"{link_grp}#{sup['ID_Usuario']}", width="stretch")
                        else:
                            st.button("🚫 SEM LINK", disabled=True, width="stretch",
                                      key=f"no_link_{sup['ID_Usuario']}")
                    with st.expander(f"👥 LISTA DE INTEGRANTES ({qtd_equipe})"):
                        if not equipe.empty:
                            for _, vol in equipe.iterrows():
                                w_vol = sanitize_whatsapp(vol.get('WhatsApp', ''))
                                render_contract_entry(vol['Nome'], w_vol)
                        else:
                            st.caption("Sem voluntários.")
                    st.markdown("<br><br>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# ABA 2: LOGS/DASHBOARD
# ------------------------------------------------------------------
with tab_logs:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>ESTATÍSTICAS DO COMANDO</h2>",
        unsafe_allow_html=True)

    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))

    if not df_logs.empty:
        ultimos_logs_raw = df_logs.tail(10)
        df_ticker = pd.merge(ultimos_logs_raw, df_usuarios[['ID_Usuario', 'Nome']],
                             on='ID_Usuario', how='left')
        df_ticker['Nome'] = df_ticker['Nome'].fillna(df_ticker['ID_Usuario'])
        mensagens_ticker = [
            f"⚡ {str(row['Nome']).split()[0].upper()}: {str(row['Tipo_Acao']).split('|')[0].strip().upper()}"
            for _, row in df_ticker[::-1].iterrows()
        ]
        render_ticker(mensagens_ticker)

    # Métricas principais
    c1, c2, c3 = st.columns(3)
    total_acoes = len(df_logs)
    usuarios_ativos = df_logs[df_logs['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
    total_contratos = carregar_dados("Contratos", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    total_contratos = len(total_contratos) if total_contratos is not None else 0

    c1.metric("Ações Totais", total_acoes)
    c2.metric("Colaboradores Ativos", usuarios_ativos)
    c3.metric("Contratos Registrados", total_contratos)

    # Tabela detalhada (últimos 20 logs)
    st.markdown("<h3 style='font-size:1.4rem;'>Últimos registros</h3>", unsafe_allow_html=True)
    st.dataframe(df_logs.tail(20)[['Data_Hora', 'ID_Usuario', 'Tipo_Acao']],
                 hide_index=True, width='stretch')

    # EXPORTAÇÃO EXCEL
    if not df_logs.empty:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_logs.to_excel(writer, index=False, sheet_name='Logs')
                writer.save()
            st.download_button(
                label="📥 BAIXAR LOGS COMPLETOS (XLSX)",
                data=buffer.getvalue(),
                file_name="comando2026_logs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro ao gerar Excel: {e}")

# ------------------------------------------------------------------
# ABA 3: MAPA
# ------------------------------------------------------------------
with tab_mapa:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>🗺️ MAPA DE OPERAÇÕES</h2>",
        unsafe_allow_html=True)

    df_logs['Data_Filtro'] = df_logs['Data_Hora'].str.split().str[0]
    datas_mapa = sorted(
        [d for d in df_logs['Data_Filtro'].unique().tolist() if isinstance(d, str) and "/" in d],
        key=lambda x: datetime.strptime(x, "%d/%m/%Y"),
        reverse=True
    )
    periodo_mapa = st.selectbox("📍 FILTRAR POR DATA", ["Histórico Completo"] + datas_mapa, key="filtro_mapa")
    if periodo_mapa == "Histórico Completo":
        df_m = df_logs.copy()
    else:
        df_m = df_logs[df_logs['Data_Filtro'] == periodo_mapa].copy()

    df_m['lat'], df_m['lon'] = zip(*df_m['Localização'].apply(
        lambda pos: (float(pos.split(",")[0]), float(pos.split(",")[1])) if isinstance(pos, str) and "," in pos else (None, None)
    ))
    df_geo = df_m.dropna(subset=['lat', 'lon'])

    if not df_geo.empty:
        mapa = folium.Map(location=[df_geo['lat'].mean(), df_geo['lon'].mean()], zoom_start=12)
        for _, row in df_geo.iterrows():
            popup = folium.Popup(f"{row['Nome']} - {row['Tipo_Acao']}", max_width=250)
            folium.Marker([row['lat'], row['lon']], popup=popup).add_to(mapa)
        st_folium(mapa, width=1200, height=600)
    else:
        st.warning("Nenhum dado de GPS encontrado para o filtro selecionado.")

# ------------------------------------------------------------------
# ABA 4: MENSAGENS / DIRETRIZES
# ------------------------------------------------------------------
with tab_mensagens:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>DIRETRIZES DO DIA</h2>",
        unsafe_allow_html=True)

    try:
        client = _get_gspread_client(st.secrets, st.session_state.get('error_log'))
        aba_msg = client.open_by_key(st.secrets["planilha"]["id"]).worksheet("Mensagens")
        dados_msg = aba_msg.get_all_records()
        df_msg = pd.DataFrame(dados_msg)

        lista_alvos = df_msg["ID_Alvo"].unique().tolist() if not df_msg.empty else []
        alvo_selecionado = st.selectbox("1. SELECIONE O GRUPO:", ["Novo..."] + lista_alvos)

        with st.form("form_admin_msg"):
            if alvo_selecionado == "Novo...":
                id_alvo, msg_i, tar = "", "", ""
            else:
                d = df_msg[df_msg["ID_Alvo"] == alvo_selecionado].iloc[-1]
                id_alvo = d.get("ID_Alvo", "")
                msg_i = d.get("Mensagem_Inicial", "")
                tar = d.get("Tarefa_Direcionada", "")

            f_id = st.text_input("ID DO GRUPO (IGUAL AO CADASTRADO):", value=id_alvo)
            f_msg = st.text_area("MENSAGEM NO POP-UP (BOAS-VINDAS):", value=msg_i, height=150)
            f_tar = st.text_area("MISSÃO DE RUA (TAREFA PRINCIPAL):", value=tar, height=100)

            if st.form_submit_button("🚀 ATUALIZAR DIRETRIZES", type="primary", width='stretch'):
                if f_id:
                    data_auto = get_agora_br().strftime("%d/%m/%Y")
                    nova_linha = [f_id, f_msg, f_tar, data_auto]
                    if alvo_selecionado != "Novo...":
                        try:
                            cell = aba_msg.find(str(alvo_selecionado))
                            if cell:
                                aba_msg.delete_rows(cell.row)
                        except Exception as e:
                            st.session_state['error_log'].append({
                                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                                'erro': str(e),
                                'funcao': 'tab_mensagens.delete',
                                'traceback': traceback.format_exc(),
                                'tipo': type(e).__name__
                            })
                    aba_msg.append_row(nova_linha)
                    st.success("✅ ATUALIZADO!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("O ID DO GRUPO É OBRIGATÓRIO")
    except Exception as e:
        st.session_state['error_log'].append({
            'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'erro': str(e),
            'funcao': 'tab_mensagens',
            'traceback': traceback.format_exc(),
            'tipo': type(e).__name__
        })
        st.error(f"Erro na conexão: {e}")

# ------------------------------------------------------------------
# ABA 5: CADASTRO DE USUÁRIOS / GRUPOS
# ------------------------------------------------------------------
with tab_cadastro:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 20px; font-size: 1.8rem;'>👤 NOVO INTEGRANTE</h2>",
        unsafe_allow_html=True)

    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_sup_only = df_usuarios[df_usuarios['Cargo'].str.lower().str.strip() == "supervisor"] if df_usuarios is not None else pd.DataFrame()
    mapeamento_sup = {
        f"{row['Nome'].upper()} ({row['ID_Usuario'].lower()})": row['ID_Usuario']
        for _, row in df_sup_only.iterrows()
    }
    lista_nomes_exibicao = sorted(mapeamento_sup.keys())

    df_grupos = carregar_grupos_completos_cached(st.secrets["planilha"]["id"])
    lista_grupos = sorted([g['ID_Grupo'] for g in df_grupos]) if df_grupos else []

    with st.container(border=True):
        with st.form("form_novo_user_v2", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**DADOS PESSOAIS**")
                n_id = st.text_input("ID / E-MAIL (LOGIN):").strip().lower()
                n_nome = st.text_input("NOME COMPLETO:")
                n_whats = st.text_input("WHATSAPP (DDD + NÚMERO):")
            with c2:
                st.markdown("**VÍNCULO NO COMANDO**")
                n_cargo = st.selectbox("CARGO:", ["Colaborador", "Supervisor", "Admin"])
                n_grupo = st.selectbox("GRUPO / TERRITÓRIO:", options=lista_grupos if lista_grupos else ["Nenhum grupo cadastrado"])
                n_sup_selecionado_display = st.selectbox(
                    "SUPERVISOR RESPONSÁVEL:",
                    options=["NENHUM / PRÓPRIO SUPERVISOR"] + lista_nomes_exibicao
                )
            if st.form_submit_button("✅ CADASTRAR INTEGRANTE", type="primary", width='stretch'):
                if n_id and n_nome and n_whats:
                    if n_grupo == "Nenhum grupo cadastrado":
                        st.error("⚠️ Cadastre pelo menos um grupo antes de criar usuários!")
                    else:
                        try:
                            client = _get_gspread_client(st.secrets, st.session_state.get('error_log'))
                            aba_u = client.open_by_key(st.secrets["planilha"]["id"]).worksheet("Usuarios")
                            id_sup_final = "" if n_sup_selecionado_display == "NENHUM / PRÓPRIO SUPERVISOR" else mapeamento_sup[n_sup_selecionado_display]
                            aba_u.append_row([n_id, n_nome.upper(), n_whats, n_cargo, n_grupo, id_sup_final])
                            st.success(f"🚀 {n_nome.upper()} CADASTRADO!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.session_state['error_log'].append({
                                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                                'erro': str(e),
                                'funcao': 'tab_cadastro.novo_usuario',
                                'traceback': traceback.format_exc(),
                                'tipo': type(e).__name__
                            })
                            st.error(f"Erro: {e}")
                else:
                    st.error("⚠️ PREENCHA TODOS OS CAMPOS!")

    # ------------------------------------------------------------------
    # SEÇÃO 2: GESTÃO DE GRUPOS E MACRO_GRUPOS
    # ------------------------------------------------------------------
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 20px; font-size: 1.8rem;'>🚩 GESTÃO DE GRUPOS E MACRO_GRUPOS</h2>",
        unsafe_allow_html=True)

    col_criar_grupo, col_criar_macro = st.columns(2)

    with col_criar_grupo:
        with st.container(border=True):
            st.markdown("**📍 CRIAR NOVO GRUPO**")
            with st.form("form_novo_grupo_simples", clear_on_submit=True):
                g_nome = st.text_input("NOME DO GRUPO (ID):", placeholder="Ex: GUARIROBA")
                g_macro = st.selectbox("MACRO_GRUPO:",
                                      options=carregar_macro_grupos_cached(st.secrets["planilha"]["id"]) or ["Nenhum Macro_Grupo cadastrado"])
                g_link = st.text_input("LINK DO GRUPO (WhatsApp):", placeholder="https://chat.whatsapp.com/...")
                if st.form_submit_button("➕ REGISTRAR GRUPO", width='stretch', type="primary"):
                    if g_nome:
                        if g_macro == "Nenhum Macro_Grupo cadastrado":
                            st.error("⚠️ Crie pelo menos um Macro_Grupo primeiro!")
                        else:
                            sucesso, msg = criar_novo_grupo(g_nome, g_macro, g_link, st.secrets, st.session_state.get('error_log'))
                            if sucesso:
                                st.success(f"✅ {msg}")
                                # Mensagem de boas vindas automática
                                try:
                                    client = _get_gspread_client(st.secrets, st.session_state.get('error_log'))
                                    plan = client.open_by_key(st.secrets["planilha"]["id"])
                                    data_atual_msg = get_agora_br().strftime("%d/%m/%Y")
                                    plan.worksheet("Mensagens").append_row([
                                        g_nome.upper(),
                                        "BEM-VINDO AO COMANDO!",
                                        "MISSÃO INICIAL DE RUA",
                                        data_atual_msg
                                    ])
                                except Exception as e:
                                    st.session_state['error_log'].append({
                                        'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                                        'erro': str(e),
                                        'funcao': 'tab_cadastro.mensagem_boas_vindas',
                                        'traceback': traceback.format_exc(),
                                        'tipo': type(e).__name__
                                    })
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    else:
                        st.error("⚠️ Digite o nome do grupo!")

    with col_criar_macro:
        with st.container(border=True):
            st.markdown("**🗺️ CRIAR NOVO MACRO_GRUPO**")
            with st.form("form_novo_macro_grupo_simples", clear_on_submit=True):
                m_nome = st.text_input("NOME DO MACRO_GRUPO:", placeholder="Ex: CEILÂNDIA/SOL NASCENTE")
                if st.form_submit_button("➕ REGISTRAR MACRO_GRUPO", width='stretch', type="primary"):
                    if m_nome:
                        sucesso, msg = criar_novo_macro_grupo(m_nome, st.secrets, st.session_state.get('error_log'))
                        if sucesso:
                            st.success(f"✅ {msg}")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("⚠️ Digite o nome do Macro_Grupo!")

    # LISTA DE GRUPOS CADASTRADOS
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 15px; font-size: 1.3rem;'>📋 GRUPOS CADASTRADOS</h3>",
        unsafe_allow_html=True)

    grupos_existentes = carregar_grupos_completos_cached(st.secrets["planilha"]["id"])
    macro_grupos_lista = carregar_macro_grupos_cached(st.secrets["planilha"]["id"])

    if grupos_existentes:
        for macro in macro_grupos_lista:
            grupos_do_macro = [g for g in grupos_existentes if g.get('Macro_Grupo', '') == macro]
            with st.expander(f"📍 {macro} ({len(grupos_do_macro)} grupos)", expanded=False):
                if grupos_do_macro:
                    for g in grupos_do_macro:
                        col_g1, col_g2 = st.columns([3, 1])
                        with col_g1:
                            st.markdown(f"**{g.get('ID_Grupo', 'N/A')}**")
                            if g.get('Link_Grupo', ''):
                                st.caption(f"🔗 [Link do Grupo]({g.get('Link_Grupo', '')})")
                        with col_g2:
                            st.caption(f"ID: {g.get('ID_Grupo', 'N/A')}")
                else:
                    st.caption("Nenhum grupo neste Macro_Grupo.")
    else:
        st.info("Nenhum grupo cadastrado.")

    st.info("💡 **Dica:** Para editar ou excluir grupos, acesse diretamente a planilha 'Grupos' no Google Sheets.")

# ------------------------------------------------------------------
# ABA 6: GESTÃO DE CONTRATOS
# ------------------------------------------------------------------
with tab_contratos:
    st.markdown(
        "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>📄 GESTÃO DE CONTRATOS</h2>",
        unsafe_allow_html=True)

    col_envio, col_status = st.columns([1.2, 2], gap="large")

    with col_envio:
        st.subheader("📤 ENVIAR PARA INTEGRANTE")
        with st.container(border=True):
            with st.form("form_admin_envia_contrato", clear_on_submit=True):
                df_destinatarios = df_usuarios[df_usuarios['Cargo'].str.lower() != "admin"]
                mapeamento_dest = {
                    f"{row['Nome'].upper()} | {row['Cargo'].upper()} | {row['ID_Grupo']}": row['ID_Usuario']
                    for _, row in df_destinatarios.iterrows()
                }
                lista_nomes_contrato = sorted(mapeamento_dest.keys())
                user_selecionado_display = st.selectbox("PARA QUEM É O CONTRATO?", options=lista_nomes_contrato)
                n_doc = st.text_input("NOME DO DOCUMENTO:", placeholder="Ex: Contrato_NomeSobrenome_Data")
                arq_pdf = st.file_uploader("ARQUIVO PDF:", type=['pdf'])
                if st.form_submit_button("🚀 ENVIAR AGORA", width='stretch', type="primary"):
                    if arq_pdf and n_doc and user_selecionado_display:
                        u_destino = mapeamento_dest[user_selecionado_display]
                        with st.spinner("Subindo para o Drive..."):
                            link = salvar_documento_drive(arq_pdf, f"ORIGINAL_{n_doc}_{u_destino}",
                                                         st.secrets, st.session_state.get('error_log'))
                            if link and registrar_novo_contrato_admin(u_destino, n_doc, link,
                                                                      st.secrets, st.session_state.get('error_log')):
                                st.success("✅ DOCUMENTO ENVIADO COM SUCESSO!")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.error("Preencha o nome do doc e selecione o PDF.")

    with col_status:
        st.subheader("📋 MONITORAMENTO")
        df_cont = carregar_dados("Contratos", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
        if df_cont is not None and not df_cont.empty:
            df_view = pd.merge(df_cont, df_usuarios[['ID_Usuario', 'Nome']], on='ID_Usuario', how='left')
            df_view['Nome'] = df_view['Nome'].fillna(df_view['ID_Usuario'])
            st.dataframe(df_view[['Nome', 'Nome_Arquivo', 'Status']],
                         column_config={
                             "Nome": "Integrante",
                             "Nome_Arquivo": "Documento",
                             "Status": "Situação"
                         },
                         width="stretch", hide_index=True)
            with st.expander("🔍 VER LINKS E ARQUIVOS", expanded=True):
                for _, row in df_view.iterrows():
                    c_info, c_links = st.columns([2, 1.5])
                    with c_info:
                        st.markdown(f"**{row['Nome'].upper()}**")
                        st.caption(f"Arquivo: {row['Nome_Arquivo']}")
                    with c_links:
                        sub_c1, sub_c2 = st.columns(2)
                        sub_c1.link_button("📄 ORIG", row['Link_Original'], width='stretch')
                        link_assin = str(row.get('Link_Assinado', ''))
                        if link_assin.startswith("http"):
                            sub_c2.link_button("✍️ ASSIN", link_assin, width='stretch', type="primary")
                        else:
                            sub_c2.button("⏳ PEND", disabled=True, width='stretch')
                    st.divider()
