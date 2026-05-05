# =============================================================================
# PAGES/01_🚀_PRINCIPAL.PY - PAINEL PRINCIPAL (PÓS-LOGIN)
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
    registrar_acao_com_pontuacao,   # ← substitui registrar_acao
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
    render_action_link_button,
    render_metric_row,
    render_contract_entry
)

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

st.set_page_config(
    page_title="COMANDO 2026",
    page_icon="🧢",
    layout="wide"
)

inject_styles()

# =============================================================================
# VERIFICAR AUTENTICAÇÃO
# =============================================================================

cookie_manager = stx.CookieManager()

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "logout_em_andamento" not in st.session_state:
    st.session_state["logout_em_andamento"] = False

if "mensagem_exibida" not in st.session_state:
    st.session_state["mensagem_exibida"] = False

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

if "last_coords" not in st.session_state:
    st.session_state["last_coords"] = "Aguardando..."

# Redirecionar se não logado
if st.session_state["usuario_logado"] is None:
    st.switch_page("pages/00_Login.py")

# =============================================================================
# CAPTURA GLOBAL DE ERROS
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

# =============================================================================
# AUTOLOGIN VIA COOKIE (SE APLICA)
# =============================================================================

todos_os_cookies = cookie_manager.get_all()

if todos_os_cookies and not st.session_state["logout_em_andamento"]:
    user_id_cookie = todos_os_cookies.get("comando2026_user_id")
    if user_id_cookie and st.session_state["usuario_logado"] is None:
        df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
        if df_usuarios is not None:
            user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == user_id_cookie.lower().strip()]
            if not user_match.empty:
                st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                st.rerun()

# =============================================================================
# VARIÁVEIS DO USUÁRIO
# =============================================================================

u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora = get_agora_br()

# =============================================================================
# SIDEBAR
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
                    registrar_acao_com_pontuacao(
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

                    registrar_acao_com_pontuacao(
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
                st.session_state['last_coords'] = "Erro GPS"
                st.markdown("🔴 **ERRO GPS**")
                st.session_state['error_log'].append({
                    'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                    'erro': str(e),
                    'funcao': 'colaborador.gps',
                    'traceback': traceback.format_exc(),
                    'tipo': type(e).__name__
                })
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
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    f"CONCLUIU: {t_txt}",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                st.success("MISSÃO REGISTRADA COM SUCESSO!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            if st.button("📸 CURTA, COMENTE E COMPARTILHE NOSSO ÚLTIMO POST!", width='stretch', key="fixo_insta"):
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    "AÇÃO: INTERAÇÃO INSTAGRAM",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                render_action_link_button(
                    texto="ABRIR PERFIL DO MAX ↗️",
                    url="https://www.instagram.com/maxmacieldf/"
                )

        with col_m2:
            if st.button("💬 TRAGA UM NOVO AMIGO PARA SER COLABORADOR!", width='stretch', key="fixo_whats"):
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    "AÇÃO: TRAZER NOVO COLABORADOR!",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
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

    st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)

# =============================================================================
# VISÃO: SUPERVISOR
# =============================================================================

elif cargo_limpo == "supervisor":

    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    m = None

    if df_msgs is not None and not df_msgs.empty:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str).str.strip() == str(u['ID_Grupo']).strip()]
        if not msg_grupo.empty:
            m = msg_grupo.iloc[-1]
            if not st.session_state["mensagem_exibida"]:
                render_info_banner(
                    titulo="Campanha Max Maciel 2026!<br><span style='color: var(--cor-secundaria);'>INFORMES DO DIA</span>",
                    subtítulo="",
                    mensagem=m['Mensagem_Inicial']
                )
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ CIENTE DAS DIRETRIZES", width='stretch', type="primary"):
                    st.session_state["mensagem_exibida"] = True
                    st.rerun()
                st.stop()

    location_data = get_geolocation()
    col_status, col_btn = st.columns([3, 1])
    with col_status:
        if location_data:
            try:
                lat, lon = location_data['coords']['latitude'], location_data['coords']['longitude']
                st.session_state['last_coords'] = f"{lat},{lon}"
                st.markdown("🟢 **GPS ATIVO**")
            except Exception as e:
                st.markdown("🔴 **ERRO GPS**")
                st.session_state['error_log'].append({
                    'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                    'erro': str(e),
                    'funcao': 'supervisor.gps',
                    'traceback': traceback.format_exc(),
                    'tipo': type(e).__name__
                })
        else:
            st.markdown("🟡 **BUSCANDO SINAL...**")
    with col_btn:
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    tab_missoes, tab_contratos, tab_equipe = st.tabs([
        "🚀 MISSÕES E PRESENÇA", "📄 MEUS CONTRATOS", "📈 ACOMPANHAMENTO"
    ])

    with tab_missoes:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        render_section_header("MEU REGISTRO")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", width='stretch', key="sup_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", width='stretch', key="sup_out"):
                modal_checkout(u, agora)

        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("🚀 MISSÕES DIÁRIAS")

        t_txt = str(m.get('Tarefa_Direcionada', 'MISSÃO GERAL')).upper() if m is not None else "MISSÃO GERAL"
        with st.container(border=True):
            st.markdown(
                f"<h3 style='text-align: center; color: var(--cor-texto); margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: var(--cor-secundaria);'>{t_txt}</p>",
                unsafe_allow_html=True)
            if st.button("CONCLUIR MISSÃO DE HOJE", width='stretch', key="sup_task_done"):
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    f"CONCLUIU: {t_txt}",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                st.success("MISSÃO REGISTRADA!")

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        cm1, cm2 = st.columns(2)
        with cm1:
            if st.button("📸 INSTAGRAM", width='stretch', key="sup_insta"):
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    "AÇÃO: INTERAÇÃO INSTAGRAM",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                render_action_link_button(
                    texto="ABRIR PERFIL ↗️",
                    url="https://www.instagram.com/maxmacieldf/"
                )
        with cm2:
            if st.button("💬 WHATSAPP", width='stretch', key="sup_whats"):
                registrar_acao_com_pontuacao(
                    u['ID_Usuario'],
                    "AÇÃO: MOBILIZAÇÃO WHATSAPP",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                msg_zap = urllib.parse.quote(
                    "Salve! Vamos juntos com Max Maciel 🚀 https://www.instagram.com/maxmacieldf/")
                render_action_link_button(
                    texto="ENVIAR P/ AMIGO ↗️",
                    url=f"https://wa.me/?text={msg_zap}"
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

    with tab_equipe:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if df_usuarios is not None and df_logs is not None:
            minha_equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str) == str(u['ID_Usuario'])]

            espaco_metricas = st.empty()

            c_data, _ = st.columns([1.5, 1])
            with c_data:
                data_sel = st.date_input("📅 DATA DE ANÁLISE", datetime.now(timezone.utc) - timedelta(hours=3))
            d_str = data_sel.strftime("%d/%m/%Y")

            logs_dia = df_logs[df_logs['Data_Hora'].str.contains(d_str)]
            ativos_dia = logs_dia[logs_dia['ID_Usuario'].isin(minha_equipe['ID_Usuario'])]
            total_vol = len(minha_equipe)
            num_ativos = ativos_dia[ativos_dia['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
            total_acoes = len(ativos_dia)

        st.markdown(f'''                                 
                <h3 style="font-size: 1.1rem; text-align: left;      
            margin-top: -15px; font-family: 'Archivo Black',         
            sans-serif; color: var(--cor-texto);">                   
                    📋 STATUS DA EQUIPE ({d_str[:5]})                
                </h3>                                                
            ''', unsafe_allow_html=True)

        for _, vol in minha_equipe.iterrows():
                logs_vol = df_logs[
                    (df_logs['ID_Usuario'] == vol['ID_Usuario']) & (df_logs['Data_Hora'].str.contains(d_str))]

                tem_in = not logs_vol[logs_vol['Tipo_Acao'].str.contains("Check-in")].empty
                tem_net = not logs_vol[logs_vol['Tipo_Acao'].str.contains("AÇÃO:")].empty
                tem_ok = not logs_vol[logs_vol['Tipo_Acao'].str.contains("CONCLUIU:")].empty

                if tem_in and tem_ok:
                    label = "🔥 COMPLETO"
                elif tem_in:
                    label = "🟢 EM CAMPO"
                elif tem_net:
                    label = "🟡 REDES"
                else:
                    label = "⚪ OFF"

                with st.expander(f"{label} | {vol['Nome'].upper()}"):
                    if not logs_vol.empty:
                        for _, row in logs_vol.tail(5)[::-1].iterrows():
                            acao_txt = str(row['Tipo_Acao']).split("|")[0].split("Foto:")[0].strip().upper()
                            hora_txt = row['Data_Hora'].split()[-1][:5]
                            fb = str(row.get('Feedback', '')).strip()
                            
                            badge = None
                            if "Check-out" in row['Tipo_Acao'] and fb and fb != "nan":
                                badge = fb.split('|')[0]
                            
                            loc = row.get('Localização', '')
                            mostrar_mapa = "," in str(loc)
                            
                            render_log_entry(
                                acao=acao_txt,
                                hora=hora_txt,
                                feedback=badge,
                                localizacao=loc if mostrar_mapa else None
                            )

                    st.divider()
                    w_vol = sanitize_whatsapp(vol['WhatsApp'])
                    p_vol = vol['Nome'].split()[0]
                    c_w1, c_w2 = st.columns(2)
                    with c_w1:
                        if tem_in:
                            b_n, b_m = "💪 MOTIVAR", f"Bora {p_vol}! Pra cima! 🚀"
                        elif tem_net:
                            b_n, b_m = "⚡ REFORÇAR", f"Boa {p_vol}! Não esquece o check-in na rua! 💪"
                        else:
                            b_n, b_m = "⚠️ COBRAR", f"Fala {p_vol}! Algum problema? Não vi suas ações hoje."
                        st.link_button(b_n,
                                       f"https://api.whatsapp.com/send?text={urllib.parse.quote(b_m)}&phone={w_vol}",
                                       width='stretch', type="primary")
                    with c_w2:
                        st.link_button("💬 CHAT", f"https://wa.me/{w_vol}", width='stretch')
        st.markdown("<br>", unsafe_allow_html=True)
        nome_primeiro = u['Nome'].split()[0].upper()
        rel_txt = f"📊 *RELATÓRIO {d_str}*\n👤 Sup: {nome_primeiro}\n👥 Equipe: {total_vol}\n🔥 Ativos: {num_ativos}\n🎯 Ações: {total_acoes}"
        st.link_button("📲 ENVIAR RELATÓRIO P/ COORDENAÇÃO",
                           f"https://api.whatsapp.com/send?text={urllib.parse.quote(rel_txt)}", width='stretch',
                           type="primary")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🛠️ SUPORTE DE LIDERANÇA</h3>", unsafe_allow_html=True)
    st.link_button("🛠️ REPORTAR ERRO NO APP", "https://wa.me/5561998788292?text=Erro no Painel de Supervisor",
                   width='stretch')

# =============================================================================
# VISÃO: ADMIN (COORDENAÇÃO)
# =============================================================================

elif cargo_limpo == "admin":

    st.markdown(f"""
        <style>
            .block-container {{
                max-width: 1100px !important; 
                padding-top: 2rem !important;
            }}
            button[data-baseweb="tab"] p {{
                font-size: 1rem !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    agora_br = get_agora_br()
    hoje_str = agora_br.strftime("%d/%m/%Y")

    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))

    if not df_logs.empty:
        ultimos_logs_raw = df_logs.tail(10)
        df_ticker = pd.merge(ultimos_logs_raw, df_usuarios[['ID_Usuario', 'Nome']], on='ID_Usuario', how='left')
        df_ticker['Nome'] = df_ticker['Nome'].fillna(df_ticker['ID_Usuario'])

        mensagens_ticker = [
            f"⚡ {str(row['Nome']).split()[0].upper()}: {str(row['Tipo_Acao']).split('|')[0].strip().upper()}"
            for _, row in df_ticker[::-1].iterrows()
        ]

        render_ticker(mensagens_ticker)

    tab_hierarquia, tab_logs, tab_mapa, tab_mensagens, tab_cadastro, tab_contratos = st.tabs([
        "👥 EQUIPES", "📊 DASHBOARD", "🗺️ MAPA", "📝 MISSÕES", "➕ CADASTRO", "📄 CONTRATOS"
    ])

    # ==============================================================
    # ABA 1: ESTRUTURA DE EQUIPES (MACRO_GRUPOS DINÂMICOS)
    # ==============================================================

    with tab_hierarquia:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: var(--cor-texto); margin-bottom: 25px; font-size: 2rem;'>ESTRUTURA DE EQUIPES</h2>",
            unsafe_allow_html=True)

        planilha_id = st.secrets["planilha"]["id"]

        # Carrega Macro_Grupos com cache (1 chamada só)
        macro_grupos_disponiveis = carregar_macro_grupos_cached(planilha_id)

        # Filtro de Macro Região
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
                        equipe = df_f_admin[
                            df_f_admin['ID_Supervisor'].astype(str).str.strip() == str(sup['ID_Usuario']).strip()]
                        qtd_equipe = len(equipe)

                        logs_eq = df_logs[(df_logs['ID_Usuario'].isin(equipe['ID_Usuario'])) & (
                            df_logs['Data_Hora'].str.contains(hoje_str))]
                        ativos_hoje = logs_eq[logs_eq['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()

                        render_team_card(
                            supervisor=sup['Nome'],
                            macro_grupo=sup['Macro_Grupo'],
                            id_grupo=sup['ID_Grupo'],
                            qtd_equipe=qtd_equipe,
                            ativos_hoje=ativos_hoje
                        )

                        raw_w_sup = str(sup.get('WhatsApp', '')).strip()
                        w_sup_limpo = sanitize_whatsapp(raw_w_sup)
                        link_grp = str(sup.get('Link_Grupo', '')).strip()

                        c_wa1, c_wa2 = st.columns(2)
                        # ---------- BOTÃO DE PONTUAR SUPERVISOR ----------
                        with c_wa1:
                            if w_sup_limpo:
                                if st.button(
                                    f"👤 FALAR COM {sup['Nome'].split()[0].upper()}",
                                    key=f"talk_{sup['ID_Usuario']}",
                                    help="Conta ponto ao supervisor (máx 1 ponto/dia)",
                                    type="primary",
                                    use_container_width=True,
                                ):
                                    # Mensagem padrão
                                    texto_msg = f"Olá {sup['Nome'].split()[0]}, tudo bem? Estou entrando em contato para acompanhar a ação de hoje."
                                    url_wa = f"https://wa.me/{w_sup_limpo}?text={urllib.parse.quote(texto_msg)}"

                                    # Registra ponto
                                    u = st.session_state["usuario_logado"]
                                    registrar_acao_com_pontuacao(
                                        id_usuario=u["ID_Usuario"],
                                        tipo_acao="talk_team",
                                        localizacao=st.session_state.get('last_coords', "Aguardando..."),
                                        feedback="",
                                        secrets=st.secrets,
                                        error_log=st.session_state.get('error_log')
                                    )
                                    # Redireciona para o WhatsApp
                                    st.markdown(
                                        f'<meta http-equiv="refresh" content="0; url={url_wa}">',
                                        unsafe_allow_html=True
                                    )
                                    st.success("✅ Mensagem enviada – ponto contabilizado!")
                                    st.rerun()
                            else:
                                st.button("👤 SEM WHATSAPP", disabled=True, width="stretch",
                                          key=f"no_wa_{sup['ID_Usuario']}")

                        # ---------- LINK DO GRUPO ----------
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

    # ==============================================================
    # As demais abas permanecem inalteradas
    # ==============================================================

    # (O restante do código da aba 'tab_mensagens', 'tab_logs', etc. continua como antes)
