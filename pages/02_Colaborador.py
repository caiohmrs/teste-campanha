# =============================================================================
# PAGES/02_🔹_COLABORADOR.PY – VISÃO COLABORADOR (bloco anteriormente em 01_Principal.py)
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
    page_title="COMANDO 2026 – Colaborador",
    page_icon="👤",
    layout="wide"
)

inject_styles()

# INICIALIZAR COOKIE MANAGER
cookie_manager = stx.CookieManager()

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# =============================================================================
# CAPTURA DE VARIÁVEIS DO USUÁRIO
# =============================================================================

u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora = get_agora_br()

# =============================================================================
# SIDEBAR (mantém a lógica original)
# =============================================================================

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

# =============================================================================
# CABEÇALHO BEM-VINDO
# =============================================================================

render_welcome_banner(u['Nome'])

# =============================================================================
# MODAIS DE PRESENÇA (DIALOG)
# =============================================================================

@st.dialog("REGISTRO DE ENTRADA")
def modal_checkin(u, agora):
    render_modal_header("INICIAR MISSÃO")

    foto_in = st.camera_input("FOTO OBRIGATÓRIA", key="cam_in_dialog")

    if st.button("CONFIRMAR CHECK-IN AGORA", width='stretch', type="primary"):
        if foto_in:
            agora_real = get_agora_br()
            gps_in = st.session_state.get('last_coords', "Sem GPS")
            with st.status("🚀 PROCESSANDO REGISTRO...", expanded=True) as status:
                nome_img = f"checkin_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link = salvar_foto_drive(foto_in, nome_img, st.secrets, st.session_state.get('error_log'))

                if link:
                    registrar_acao(
                        u['ID_Usuario'],
                        f"Check-in | Foto: {link}",
                        localizacao=gps_in,
                        feedback="",
                        secrets=st.secrets,
                        error_log=st.session_state.get('error_log')
                    )
                    try:
                        horario_formatado = agora_real.strftime("%Y-%m-%d %H:%M:%S")
                        cookie_manager.set("comando2026_checkin_time", horario_formatado)
                    except Exception as e:
                        st.session_state['error_log'].append({
                            'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                            'erro': str(e),
                            'funcao': 'modal_checkin.cookie_set',
                            'traceback': traceback.format_exc(),
                            'tipo': type(e).__name__
                        })

                    status.update(label="✅ ENTRADA REGISTRADA!", state="complete")
                    time.sleep(2)
                    st.rerun()
        else:
            st.error("⚠️ VOCÊ PRECISA TIRAR A FOTO!")


@st.dialog("REGISTRO DE SAÍDA")
def modal_checkout(u, agora):
    render_modal_header("FINALIZAR MISSÃO")

    foto_out = st.camera_input("FOTO OBRIGATÓRIA", key="cam_out_dialog")
    st.divider()

    st.markdown("### 📊 RELATO DO DIA")
    clima = st.select_slider(
        "COMO FOI O TRABALHO HOJE?",
        options=["⚠️ DIFÍCIL", "😐 NORMAL", "🔥 EXCELENTE"],
        value="😐 NORMAL"
    )
    obs = st.text_area("OBSERVAÇÕES:", placeholder="Ex: chuva, falta de material...", height=80)

    if st.button("CONFIRMAR SAÍDA", width='stretch', type="primary"):
        if foto_out:
            agora_real = get_agora_br()
            gps_out = st.session_state.get('last_coords', "Sem GPS")

            with st.spinner("📡 ENVIANDO DADOS..."):
                nome_img = f"checkout_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link_drive = salvar_foto_drive(foto_out, nome_img, st.secrets, st.session_state.get('error_log'))

                if link_drive:
                    acao_texto = f"Check-out | Foto: {link_drive}"
                    feedback_texto = f"{clima} | Obs: {obs if obs else 'Nenhuma'}"

                    registrar_acao(
                        u['ID_Usuario'],
                        acao_texto,
                        localizacao=gps_out,
                        feedback=feedback_texto,
                        secrets=st.secrets,
                        error_log=st.session_state.get('error_log')
                    )

                    try:
                        if "comando2026_checkin_time" in cookie_manager.get_all():
                            cookie_manager.delete("comando2026_checkin_time")
                    except Exception as e:
                        st.session_state['error_log'].append({
                            'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                            'erro': str(e),
                            'funcao': 'modal_checkout.cookie_delete',
                            'traceback': traceback.format_exc(),
                            'tipo': type(e).__name__
                        })

                    st.success("✅ TUDO SALVO! BOM DESCANSO.")
                    time.sleep(2)
                    st.rerun()
        else:
            st.error("⚠️ VOCÊ PRECISA TIRAR A FOTO PARA ENCERRAR!")

# =============================================================================
# VISÃO: COLABORADOR
# =============================================================================

if cargo_limpo == "colaborador":

    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    m = None

    hoje_str = agora.strftime("%d/%m/%Y")
    meus_logs_hoje = df_logs[(df_logs['ID_Usuario'] == u['ID_Usuario']) & (
        df_logs['Data_Hora'].str.contains(hoje_str))] if df_logs is not None else pd.DataFrame()
    qtd_acoes_hoje = len(meus_logs_hoje)

    render_status_bar(qtd_acoes_hoje, qtd_acoes_hoje > 0)

    if df_msgs is not None and not df_msgs.empty:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str).str.strip() == str(u['ID_Grupo']).strip()]

        if not msg_grupo.empty:
            m = msg_grupo.iloc[-1]

            if not st.session_state["mensagem_exibida"]:
                render_info_banner(
                    titulo="Campanha Max Maciel 2026!<br><span style='color: var(--cor-secundaria);'>INFORME DO DIA</span>",
                    subtítulo="",
                    mensagem=m['Mensagem_Inicial']
                )
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ LI AS INSTRUÇÕES E QUERO ENTRAR", width='stretch', type="primary"):
                    st.session_state["mensagem_exibida"] = True
                    st.rerun()
                st.stop()

    location_data = get_geolocation()
    col_status, col_btn = st.columns([3, 1])
    with col_status:
        if location_data:
            try:
                lat = location_data['coords']['latitude']
                lon = location_data['coords']['longitude']
                st.session_state['last_coords'] = f"{lat},{lon}"
                st.markdown("🟢 **GPS ATIVO**")
            except Exception as e:
                st.session_state['error_log'].append({
                    'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                    'erro': str(e),
                    'funcao': 'colaborador.gps',
                    'traceback': traceback.format_exc(),
                    'tipo': type(e).__name__
                })
                st.session_state['last_coords'] = "Erro GPS"
                st.markdown("🔴 **ERRO GPS**")
        else:
            st.session_state['last_coords'] = "Aguardando..."
            st.markdown("🟡 **BUSCANDO SINAL...**")
    with col_btn:
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

    with tab_missoes:
        render_section_header("REGISTRO DE PRESENÇA")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", width='stretch', key="btn_modal_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", width='stretch', key="btn_modal_out"):
                modal_checkout(u, agora)

        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("🚀 MISSÕES DIÁRIAS")

        t_txt = ""
        if m is not None:
            val_planilha = str(m.get('Tarefa_Direcionada', '')).strip()
            if val_planilha.lower() != 'nan' and val_planilha != "":
                t_txt = val_planilha.upper()

        if not t_txt:
            t_txt = "MOBILIZAÇÃO GERAL E PANFLETAGEM"

        with st.container(border=True):
            st.markdown(
                f"<h3 style='text-align: center; color: var(--cor-texto); margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: var(--cor-secundaria);'>{t_txt}</p>",
                unsafe_allow_html=True)

            if st.button(f"CONCLUIR MISSÃO DE HOJE", width='stretch', key="btn_tarefa_fixa"):
                registrar_acao(u['ID_Usuario'], f"CONCLUIU: {t_txt}", localizacao=st.session_state.get('last_coords'),
                               feedback="", secrets=st.secrets, error_log=st.session_state.get('error_log'))
                st.success("MISSÃO REGISTRADA COM SUCESSO!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            if st.button("📸 CURTA, COMENTE E COMPARTILHE NOSSO ÚLTIMO POST!", width='stretch', key="fixo_insta"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: INTERAÇÃO INSTAGRAM",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                render_action_link_button(
                    texto="ABRIR PERFIL DO MAX ↗️",
                    url="https://www.instagram.com/maxmacieldf/"
                )

        with col_m2:
            if st.button("💬 TRAGA UM NOVO AMIGO PARA SER COLABORADOR!", width='stretch', key="fixo_whats"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: TRAZER NOVO COLABORADOR!",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                mensagem_pronta = "Salve! Já acompanha o trabalho do Max Maciel pelo DF?? Sou colaborador dele e estou muito feliz com o trabalho que estamos fazendo. Vamos juntos nessa campanha? 🚀 https://forms.gle/NzJy6NEynbaPyD6w6"
                msg_url = urllib.parse.quote(mensagem_pronta)
                render_action_link_button(
                    texto="ESCOLHER AMIGO ↗️",
                    url=f"https://wa.me/?text={msg_url}"
                )

    with tab_contratos:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        render_section_header("📝 NOVO CONTRATO")

        url_formulario = "https://forms.gle/9fqxvN8XfCmTRh9EA"
        st.link_button("📋 PREENCHER DADOS PARA GERAR CONTRATO", url_formulario, width='stretch', type="primary")

        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        st.divider()

        st.subheader("📄 Meus Documentos")
        df_contratos = carregar_dados("Contratos", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
        if df_contratos is not None:
            meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
            if not meus_docs.empty:
                for _, doc in meus_docs.iterrows():
                    with st.container(border=True):
                        st.write(f"**Doc:** {doc['Nome_Arquivo']}")
                        st.link_button("📥 Baixar Original", doc['Link_Original'], width='stretch')
                        arq = st.file_uploader("Upload Assinado (PDF)", type=['pdf'], key=f"up_{doc['Nome_Arquivo']}")
                        if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}", width='stretch',
                                     type="primary"):
                            if arq:
                                with st.spinner("Enviando..."):
                                    link = salvar_documento_drive(arq, f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}",
                                                                  st.secrets, st.session_state.get('error_log'))
                                    if link and atualizar_contrato_enviado(u['ID_Usuario'], doc['Nome_Arquivo'], link,
                                                                           st.secrets, st.session_state.get('error_log')):
                                        st.success("Enviado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
            else:
                st.info("Nenhum contrato pendente.")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🆘 PRECISA DE AJUDA?</h3>", unsafe_allow_html=True)

    col_sup1, col_sup2 = st.columns(2)
    id_supervisor_dele = str(u.get('ID_Supervisor', '')).strip().lower()
    dados_supervisor = df_usuarios[df_usuarios[
                                       'ID_Usuario'].str.lower().str.strip() == id_supervisor_dele] if df_usuarios is not None else pd.DataFrame()

    with col_sup1:
        if not dados_supervisor.empty:
            whats_sup = sanitize_whatsapp(dados_supervisor.iloc[0]['WhatsApp'])
            nome_sup = dados_supervisor.iloc[0]['Nome'].split()[0].upper()
            msg_sup = f"Olá {nome_sup}! Sou colaborador da sua equipe e preciso de ajuda."
            st.link_button(f"👤 FALAR COM {nome_sup}", f"https://wa.me/{whats_sup}?text={urllib.parse.quote(msg_sup)}",
                           width='stretch')
        else:
            st.button("👤 SUPERVISOR NÃO ENCONTRADO", disabled=True, width='stretch')

    with col_sup2:
        whats_tecnico = "5561998788292"
        msg_tecnica = "Olá! Estou tendo dificuldades técnicas com o aplicativo Comando 2026."
        st.link_button("🛠️ SUPORTE DO APP", f"https://wa.me/{whats_tecnico}?text={urllib.parse.quote(msg_tecnica)}",
                       width='stretch')
