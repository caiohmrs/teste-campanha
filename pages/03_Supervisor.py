# =============================================================================
# PAGES/03_🔸_SUPERVISOR.PY – VISÃO SUPERVISOR (bloco anteriormente em 01_Principal.py)
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
from typing import List, Any, Dict  # ← novo import de tipagem

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
    render_progress_bar,
    render_leaderboard,
    render_position_badge,
    render_points_badge,
    render_action_progress,
    render_info_ranking,
    render_material_form,          # <-- INCLUIR AQUI
    render_material_summary,
)

# ← novos imports de gamificação
from utils.gamification import PONTUACAO, LIMITE_DIARIO, ACTION_LABELS

# CONFIGURAÇÃO INICIAL
st.set_page_config(
    page_title="COMANDO 2026 – Supervisor",
    page_icon="🧑‍💼",
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
# 1️⃣ Garantir que a sessão tenha a chave "usuario_logado"
# ----------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# ----------------------------------------------------------------------
# 2️⃣ Se não houver usuário logado, enviar para a tela de login
# ----------------------------------------------------------------------
if st.session_state["usuario_logado"] is None:
    # limpa possíveis caches que já foram criados antes do redirect
    st.cache_data.clear()
    st.switch_page("pages/00_Login.py")
# CAPTURA DE VARIÁVEIS DO USUÁRIO
u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora = get_agora_br()

# SIDEBAR (mantém a mesma lógica de logout etc.)
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

# CABEÇALHO BEM-VINDO
render_welcome_banner(u['Nome'])

# MODAIS DE PRESENÇA (mesmo código dos dialogs)
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
                    registrar_acao(u['ID_Usuario'], f"Check-in | Foto: {link}", localizacao=gps_in,
                                   feedback="", secrets=st.secrets, error_log=st.session_state.get('error_log'))
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
                    registrar_acao(u['ID_Usuario'], acao_texto,
                                   localizacao=gps_out,
                                   feedback=feedback_texto, secrets=st.secrets,
                                   error_log=st.session_state.get('error_log'))
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

# VISÃO: SUPERVISOR
if cargo_limpo == "supervisor":

    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"], st.session_state.get('error_log'))

    # --------------------------------------------------------------
    #  ⚡ Leaderboard – carregar dados para o ranking do supervisor
    # --------------------------------------------------------------
    df_leaderboard = carregar_dados(
        "Leaderboard",
        st.secrets["planilha"]["id"],
        st.session_state.get('error_log')
    )

    # Variáveis auxiliares (mesmas usadas no colaborador)
    pontos_hoje = 0
    total_pontos = 0
    posicao_atual = None
    acoes_progresso: List[Dict[str, Any]] = []
    ranking: List[Dict[str, Any]] = []

    if df_leaderboard is not None and not df_leaderboard.empty:
        hoje_str = agora.strftime("%d/%m/%Y")
        linhas_hoje = df_leaderboard[df_leaderboard['data_dia'] == hoje_str]

        # --------------------------------------------------------------
        # 1️⃣ Resumo das ações hoje (para o card de progresso - opcional)
        # --------------------------------------------------------------
        for acao, _ in PONTUACAO.items():
            limite = LIMITE_DIARIO.get(acao)               # None → ilimitado
            feitas = len(linhas_hoje[linhas_hoje['tipo_acao'] == acao])
            # O resumo não é usado diretamente aqui, mas pode servir para debug

        # --------------------------------------------------------------
        # 2️⃣ Métricas do supervisor (pontos de hoje, total acumulado, etc.)
        # --------------------------------------------------------------
        df_user = df_leaderboard[df_leaderboard['id_usuario'] == u['ID_Usuario']]
        if not df_user.empty:
            pontos_hoje = int(df_user[df_user['data_dia'] == hoje_str]['pontos_ganhos'].astype(int).sum())
            total_pontos = int(df_user.iloc[-1]['pontos_total'])

        # --------------------------------------------------------------
        # 3️⃣ Ranking geral (top 10) – apenas supervisores
        # --------------------------------------------------------------
        # a) Última atualização de cada usuário
        df_ultimas = df_leaderboard.sort_values('ultima_atualizacao') \
                                   .drop_duplicates('id_usuario', keep='last')

        # b) Unir com a planilha de usuários para obter o cargo
        df_usuarios_tmp = df_usuarios[['ID_Usuario', 'Cargo']].rename(columns={'ID_Usuario': 'id_usuario'})
        df_ultimas = df_ultimas.merge(df_usuarios_tmp, on='id_usuario', how='left')

        # c) Filtrar somente usuários cujo cargo contém “supervisor”
        df_ultimas = df_ultimas[
            df_ultimas['Cargo'].astype(str).str.lower().str.contains('supervisor')
        ]

        # d) Ordenar por pontuação total (desc) e recomputar a posição
        df_ordenado = df_ultimas.sort_values('pontos_total', ascending=False).reset_index(drop=True)
        df_ordenado['posicao'] = df_ordenado.index + 1

        # e) Garantir que a coluna de ganhos seja numérica
        df_ordenado['pontos_ganhos'] = (
            pd.to_numeric(df_ordenado['pontos_ganhos'], errors='coerce')
            .fillna(0)
            .astype(int)
        )

        # f) Converter para a lista esperada por render_leaderboard()
        ranking = df_ordenado[['posicao', 'nome', 'pontos_total', 'pontos_ganhos']].rename(
            columns={
                'nome'        : 'nome',
                'pontos_total': 'pontos',
                'pontos_ganhos': 'ganho'
            }
        ).to_dict('records')

        # g) Posição atual do supervisor (após filtro)
        linha_user = df_ordenado[df_ordenado['id_usuario'] == u['ID_Usuario']]
        if not linha_user.empty:
            posicao_atual = int(linha_user.iloc[0]['posicao'])

        # --------------------------------------------------------------
        # 4️⃣ Lista de progresso das minhas ações (para o componente)
        # --------------------------------------------------------------
        df_user_today = df_leaderboard[
            (df_leaderboard['id_usuario'] == u['ID_Usuario']) &
            (df_leaderboard['data_dia'] == hoje_str)
        ]

        for acao, pts_por_acao in PONTUACAO.items():
            limite = LIMITE_DIARIO.get(acao)                 # None = sem limite
            feitas = int(df_user_today[df_user_today['tipo_acao'] == acao].shape[0])
            nome_elegante = ACTION_LABELS.get(acao, acao.replace('_', ' ').title())
            acoes_progresso.append({
                "nome"   : nome_elegante,
                "feitas" : feitas,
                "limite" : limite,
                "pontos" : pts_por_acao
            })

    # ----------------------------------------------------------------------
    # Mensagem do dia (variável de mensagem)
    # ----------------------------------------------------------------------
    m = None  # <-- mantido para compatibilidade com código abaixo
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
                st.session_state['error_log'].append({
                    'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                    'erro': str(e),
                    'funcao': 'supervisor.gps',
                    'traceback': traceback.format_exc(),
                    'tipo': type(e).__name__
                })
                st.markdown("🔴 **ERRO GPS**")
        else:
            st.markdown("🟡 **BUSCANDO SINAL...**")
    with col_btn:
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    tab_missoes, tab_contratos, tab_equipe, tab_ranking = st.tabs([
        "🚀 MISSÕES E PRESENÇA", "📄 MEUS CONTRATOS", "📈 ACOMPANHAMENTO", "🏆 Ranking"
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
                registrar_acao(u['ID_Usuario'], f"CONCLUIU MISSÃO DE HOJE: {t_txt}",
                               localizacao=st.session_state.get('last_coords'), feedback="",
                               secrets=st.secrets, error_log=st.session_state.get('error_log'))
                st.success("MISSÃO REGISTRADA!")

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        cm1, cm2 = st.columns(2)
        with cm1:
            if st.button("📸 CURTA COMENTE E COMPARTILHE O ÚLTIMO POST DO INSTA!", width='stretch', key="sup_insta"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: INTERAÇÃO INSTAGRAM",
                               localizacao=st.session_state.get('last_coords'), feedback="",
                               secrets=st.secrets, error_log=st.session_state.get('error_log'))
                render_action_link_button(
                    texto="ABRIR PERFIL ↗️",
                    url="https://www.instagram.com/maxmacieldf/"
                )
        with cm2:
            if st.button("💬 CHAME UM AMIGO PARA SER VOLUNTÁRIO", width='stretch', key="sup_whats"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: TRAZER NOVO COLABORADOR NO WHATSAPP!",
                               localizacao=st.session_state.get('last_coords'), feedback="",
                               secrets=st.secrets, error_log=st.session_state.get('error_log'))
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
        st.subheader("📄 MEUS DOCUMENTOS")
        df_contratos = carregar_dados("Contratos", st.secrets["planilha"]["id"], st.session_state.get('error_log'))
        if df_contratos is not None:
            meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
            if not meus_docs.empty:
                for _, doc in meus_docs.iterrows():
                    with st.container(border=True):
                        st.write(f"**Doc:** {doc['Nome_Arquivo']}")
                        st.link_button("📥 Baixar Original", doc['Link_Original'], width='stretch')
                        arq = st.file_uploader("Upload Assinado (PDF)", type=['pdf'],
                                               key=f"up_{doc['Nome_Arquivo']}")
                        if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}",
                                     width='stretch', type="primary"):
                            if arq:
                                with st.spinner("Enviando..."):
                                    link = salvar_documento_drive(arq,
                                                                f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}",
                                                                st.secrets,
                                                                st.session_state.get('error_log'))
                                    if link and atualizar_contrato_enviado(u['ID_Usuario'],
                                                                           doc['Nome_Arquivo'],
                                                                           link,
                                                                           st.secrets,
                                                                           st.session_state.get('error_log')):
                                        st.success("Enviado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
            else:
                st.info("Nenhum contrato pendente.")

    with tab_equipe:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if df_usuarios is not None and df_logs is not None:
            # ------------------------------------------------------------------
            # Equipe do supervisor
            # ------------------------------------------------------------------
            minha_equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str) == str(u['ID_Usuario'])]
            
            # --------- NOVO BLOCOS ----------
            # Lista de colaboradores (ID + Nome) que pertencem ao supervisor
            colaboradores = [
                (str(vol['ID_Usuario']), vol['Nome'])
                for _, vol in minha_equipe.iterrows()
            ]

            # Tipos de material disponíveis (pode ser estendido futuramente)
            tipos_material = [
                "Água",
                "Máscara",
                "Kit de primeiros socorros",
                "Alimento",
                "Outro"
            ]

            st.subheader("📦 Controle de Materiais da Equipe")
            render_material_form(st.secrets)          # <-- CHAMADA ATUALIZADA
            st.markdown("---")
            # --------------------------------

            espaco_metricas = st.empty()
            c_data, _ = st.columns([1.5, 1])
            with c_data:
                data_sel = st.date_input("📅 DATA DE ANÁLISE",
                                        datetime.now(timezone.utc) - timedelta(hours=3))
            d_str = data_sel.strftime("%d/%m/%Y")
            logs_dia = df_logs[df_logs['Data_Hora'].str.contains(d_str)]
            ativos_dia = logs_dia[logs_dia['ID_Usuario'].isin(minha_equipe['ID_Usuario'])]
            total_vol = len(minha_equipe)
            num_ativos = ativos_dia[ativos_dia['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
            total_acoes = len(ativos_dia)

            st.markdown(f'''
                <h3 style="font-size: 1.1rem; text-align: left; margin-top: -15px; font-family: 'Archivo Black', sans-serif; color: var(--cor-texto);'>
                    📋 STATUS DA EQUIPE ({d_str[:5]})
                </h3>
                ''', unsafe_allow_html=True)

            for _, vol in minha_equipe.iterrows():
                logs_vol = df_logs[
                    (df_logs['ID_Usuario'] == vol['ID_Usuario']) &
                    (df_logs['Data_Hora'].str.contains(d_str))
                ]
                tem_in = not logs_vol[logs_vol['Tipo_Acao'].str.contains("Check-in")].empty
                tem_net = not logs_vol[logs_vol['Tipo_Acao'].str.contains("AÇÃO:")].empty
                tem_ok = not logs_vol[logs_vol['Tipo_Acao'].str.contains("CONCLUIR:")].empty

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
                       f"https://api.whatsapp.com/send?text={urllib.parse.quote(rel_txt)}",
                       width='stretch')

    # ----------------------------------------------------------------------
    # Aba Ranking – accordion (expander) para melhor usabilidade
    # ----------------------------------------------------------------------
    with tab_ranking:
        # -------------------------------------------------------------
        # 1️⃣ Explicação do Ranking
        # -------------------------------------------------------------
        with st.expander("⚙️ Como funciona o Ranking", expanded=False):
            render_info_ranking(
                titulo="Como funciona o Ranking",
                mensagem=(
                    "As ações de CheckIn, CheckOut, Completar a Missão do dia, Interagir no Insta e Convidar um novo amigo pelo whatsapp gera pontuação. "
                    "Cada ação tem um limite diário e uma pontuação concedida (veja abaixo no progresso de ações). "
                    "Somente as ações aprovadas aumentam o total de pontos."
                )
            )

        # -------------------------------------------------------------
        # 2️⃣ Progresso das Ações do Usuário
        # -------------------------------------------------------------
        with st.expander("🚀 Progresso das minhas ações", expanded=False):
            if acoes_progresso:
                render_action_progress(acoes_progresso)
            else:
                st.info("Nenhuma ação realizada ainda.")

        # -------------------------------------------------------------
        # 3️⃣ Leaderboard Geral
        # -------------------------------------------------------------
        # **Leaderboard – agora exibido fora de qualquer expander**
        if ranking:
            render_leaderboard(ranking)
        else:
            st.info("Ainda não há dados de pontuação para exibir.")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🆘 PRECISA DE AJUDA?</h3>", unsafe_allow_html=True)

    col_sup1, col_sup2 = st.columns(2)
    id_supervisor_dele = str(u.get('ID_Supervisor', '')).strip().lower()
    dados_supervisor = df_usuarios[df_usuarios[
                                       'ID_Usuario'].str.lower().str.strip() == id_supervisor_dele] if df_usuarios is not None else pd.DataFrame()

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🛠️ SUPORTE DE LIDERANÇA</h3>", unsafe_allow_html=True)
    st.link_button("🛠️ REPORTAR ERRO NO APP",
                   "https://wa.me/5561998788292?text=Erro no Painel de Supervisor",
                   width='stretch')
