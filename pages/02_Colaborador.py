# pages/02_Colaborador.py
# -------------------------------------------------
# VISÃO COLABORADOR – módulo extraído de 01_Principal.py
# -------------------------------------------------
import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
import time
import urllib.parse
import traceback
from datetime import datetime

from streamlit_js_eval import get_geolocation

from utils.styles import inject_styles
from utils.components import (
    render_welcome_banner,
    render_status_bar,
    render_section_header,
    render_modal_header,
    render_info_banner,
    render_ticker,
    render_metric_card,
    render_action_link_button,
    render_metric_row,
)

from funcoes import (
    carregar_dados,
    get_agora_br,
    validar_gps_basico,
    sanitize_whatsapp,
    obter_endereco_simples,
    registrar_acao,
)


def render_colaborador(u, agora):
    """
    Renderiza toda a interface exibida quando o usuário tem cargo “colaborador”.
    """
    # -------------------------------------------------
    #  INÍCIO – mantém exatamente o que estava aqui
    # -------------------------------------------------
    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    m = None

    hoje_str = agora.strftime("%d/%m/%Y")
    meus_logs_hoje = (
        df_logs[
            (df_logs['ID_Usuario'] == u['ID_Usuario']) &
            (df_logs['Data_Hora'].str.contains(hoje_str))
        ] if df_logs is not None else pd.DataFrame()
    )
    qtd_acoes_hoje = len(meus_logs_hoje)

    render_status_bar(qtd_acoes_hoje, qtd_acoes_hoje > 0)

    # -------- Mensagem do dia (caso exista) --------
    if df_msgs is not None and not df_msgs.empty:
        msg_grupo = df_msgs[
            df_msgs['ID_Alvo'].astype(str).str.strip() == str(u['ID_Grupo']).strip()
        ]

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

    # -------- GPS / Sinal --------
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

    # -------- TABS (Missões / Contratos) --------
    tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

    # ------------------- TAB MISSOES -------------------
    with tab_missoes:
        render_section_header("REGISTRO DE PRESENÇA")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", width='stretch', key="btn_modal_in"):
                # Chamando modal definido em 01_Principal.py
                from pages.01_Principal import modal_checkin
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", width='stretch', key="btn_modal_out"):
                from pages.01_Principal import modal_checkout
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
                registrar_acao(
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

        # ---- Instagram ----
        with col_m1:
            if st.button("📸 CURTA, COMENTE E COMPARTILHE NOSSO ÚLTIMO POST!", width='stretch', key="fixo_insta"):
                registrar_acao(
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

        # ---- WhatsApp ----
        with col_m2:
            if st.button("💬 TRAGA UM NOVO AMIGO PARA SER COLABORADOR!", width='stretch', key="fixo_whats"):
                registrar_acao(
                    u['ID_Usuario'],
                    "AÇÃO: TRAZER NOVO COLABORADOR!",
                    localizacao=st.session_state.get('last_coords'),
                    feedback="",
                    secrets=st.secrets,
                    error_log=st.session_state.get('error_log')
                )
                mensagem_pronta = (
                    "Salve! Já acompanha o trabalho do Max Maciel pelo DF?? "
                    "Sou colaborador dele e estou muito feliz com o trabalho que estamos "
                    "fazendo. Vamos juntos nessa campanha? 🚀 https://forms.gle/NzJy6NEynbaPyD6w6"
                )
                url_msg = urllib.parse.quote(mensagem_pronta)
                render_action_link_button(
                    texto="ESCOLHER AMIGO ↗️",
                    url=f"https://wa.me/?text={url_msg}"
                )

    # ------------------- TAB CONTRATOS -------------------
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
                                    from funcoes import salvar_documento_drive, atualizar_contrato_enviado
                                    link = salvar_documento_drive(
                                        arq,
                                        f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}",
                                        st.secrets,
                                        st.session_state.get('error_log')
                                    )
                                    if link and atualizar_contrato_enviado(
                                        u['ID_Usuario'],
                                        doc['Nome_Arquivo'],
                                        link,
                                        st.secrets,
                                        st.session_state.get('error_log')
                                    ):
                                        st.success("Enviado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
            else:
                st.info("Nenhum contrato pendente.")
    # -------------------------------------------------
    #  FIM – tudo o que estava aqui permanece intacto
    # -------------------------------------------------
