# =============================================================================
# COMPONENTS.PY - COMPONENTES REUTILIZÁVEIS "COMANDO 2026"
# =============================================================================
# 
# Este arquivo contém funções que renderizam componentes HTML/CSS reutilizáveis.
# Todos os estilos estão definidos em utils/styles.py
# 
# =============================================================================

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from utils.gamification import ACTION_LABELS   # ← novo import
import funcoes as fn                  # <-- IMPORTAÇÃO PADRÃO (como nos outros componentes)


def render_login_header():
    """Renderiza o cabeçalho da tela de login."""
    st.markdown(f"""
        <h1 class="login-header">
            Max Maciel<br><span class="login-header-subtitle">🧢 2026</span>
        </h1>
    """, unsafe_allow_html=True)


def render_login_box():
    """Renderiza a caixa de login."""
    st.markdown("""
        <div class="login-box">
            <h2>Faça seu login abaixo:</h2>
        </div>
    """, unsafe_allow_html=True)


def render_welcome_banner(nome_usuario):
    """Renderiza o banner de boas‑vindas do usuário."""
    nome_primeiro = nome_usuario.split()[0].upper()
    st.markdown(f"""
        <div class="welcome-banner">
            <h3 class="welcome-banner-title">BEM‑VINDO,</h3>
            <h1 class="welcome-banner-name">{nome_primeiro}</h1>
        </div>
    """, unsafe_allow_html=True)


def render_status_bar(qtd_acoes, ativo):
    """Renderiza a barra de status (ações hoje + status)."""
    status_texto = "ATIVO" if qtd_acoes > 0 else "OFF"
    st.markdown(f"""
        <div class="status-bar">
            <span class="status-bar-item">
                <span class="status-bar-dot">●</span> AÇÕES HOJE: {qtd_acoes}
            </span>
            <span class="status-bar-item">
                <span class="status-bar-dot">●</span> STATUS: {status_texto}
            </span>
        </div>
    """, unsafe_allow_html=True)


def render_section_header(titulo):
    """Renderiza um cabeçalho de seção."""
    st.markdown(f"""
        <div class="section-header">
            <h2>{titulo}</h2>
        </div>
    """, unsafe_allow_html=True)


def render_modal_header(titulo):
    """Renderiza o cabeçalho de um modal/dialog."""
    st.markdown(f"""
        <div class="modal-header">
            <h2>{titulo}</h2>
        </div>
    """, unsafe_allow_html=True)


def render_info_banner(titulo, subtítulo, mensagem):
    """Renderiza o banner de informações do dia."""
    st.markdown(f"""
        <div class="info-banner">
            <h1>{titulo}<br><span class="info-banner-subtitle">{subtítulo}</span></h1>
            <hr>
            <p>{mensagem}</p>
        </div>
    """, unsafe_allow_html=True)


def render_ticker(mensagens):
    """Renderiza o ticker animado de ações recentes (Admin)."""
    frase = "  ///  ".join(mensagens)
    conteudo_duplicado = f"{frase} /// {frase}"
    st.markdown(f"""
        <div class="ticker-container">
            <div class="ticker-content">
                {conteudo_duplicado}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_team_card(supervisor, macro_grupo, id_grupo, qtd_equipe, ativos_hoje):
    """Renderiza um card de equipe (Supervisor/Admin)."""
    cor_ativos = "var(--cor-secundaria)" if ativos_hoje > 0 else "#666666"
    st.markdown(f"""
        <div class="team-card">
            <div class="team-card-header">
                <div>
                    <h3 class="team-card-name">{supervisor}</h3>
                    <span class="team-card-macro">MACRO: {macro_grupo}</span>
                </div>
                <span class="team-card-badge">{id_grupo}</span>
            </div>
            <div style="display: flex; gap: 15px;">
                <div class="team-card-metric">
                    <div class="team-card-metric-label">EQUIPE</div>
                    <div class="team-card-metric-value">{qtd_equipe}</div>
                </div>
                <div class="team-card-metric">
                    <div class="team-card-metric-label">ATIVOS</div>
                    <div class="team-card-metric-value" style="color: {cor_ativos};">{ativos_hoje}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_metric_card(label, value, secondary=False):
    """Renderiza um card de métrica."""
    classe_valor = "metric-card-value-secondary" if secondary else ""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-label">{label}</div>
            <div class="metric-card-value {classe_valor}">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def render_support_panel():
    """Renderiza o painel de suporte técnico."""
    st.markdown("""
        <div class="support-panel">
            <h1>🛠️ PAINEL DE SUPORTE TÉCNICO</h1>
            <p>DEBUG • MONITORAMENTO • DIAGNÓSTICO</p>
        </div>
    """, unsafe_allow_html=True)


def render_diagnostic_card(titulo, status, mensagem, cor_fundo):
    """Renderiza um card de diagnóstico."""
    st.markdown(f"""
        <div class="diagnostic-card" style="background-color: {cor_fundo};">
            <h3>{titulo}</h3>
            <p class="diagnostic-card-status">{status}</p>
            <p class="diagnostic-card-msg">{mensagem}</p>
        </div>
    """, unsafe_allow_html=True)


def render_log_entry(acao, hora, feedback=None, localizacao=None):
    """Renderiza uma entrada de log."""
    badge_html = ""
    if feedback and "Check-out" in acao:
        badge_html = f'<span class="log-entry-badge">{feedback.split("|")[0]}</span>'
    
    mapa_html = ""
    if localizacao and "," in str(localizacao):
        mapa_html = f'''<div>
            <a href="https://www.google.com/maps?q={localizacao}" target="_blank" class="log-entry-map-btn">📍 MAPA</a>
        </div>'''
    
    st.markdown(f'''
        <div class="log-entry">
            <div style="text-align:left;">
                <span class="log-entry-action">{acao}</span>{badge_html}
                <br><span class="log-entry-time">🕒 {hora}</span>
            </div>
            {mapa_html}
        </div>
    ''', unsafe_allow_html=True)


def render_contract_entry(nome, whatsapp):
    """Renderiza uma entrada de contrato/colaborador."""
    st.markdown(f"""
        <div class="contract-card">
            <span class="contract-card-name">{nome.upper()}</span>
            <a href="https://wa.me/{whatsapp}" target="_blank" class="contract-card-btn">CHAMAR</a>
        </div>
    """, unsafe_allow_html=True)


def render_action_link_button(texto, url):
    """Renderiza um botão de link de ação."""
    st.markdown(f"""
        <a href="{url}" target="_blank">
            <div class="action-link-btn">{texto}</div>
        </a>
    """, unsafe_allow_html=True)


def render_metric_row(metrics):
    """
    Renderiza uma linha de métricas pequenas.
    
    Args:
        metrics: Lista de dicionários com 'label', 'value', 'secondary' (opcional)
    """
    items_html = ""
    for m in metrics:
        classe_valor = "metric-row-value-secondary" if m.get('secondary', False) else ""
        items_html += f"""
            <div class="metric-row-item">
                <p class="metric-row-label">{m['label']}</p>
                <p class="metric-row-value {classe_valor}">{m['value']}</p>
            </div>
        """
    
    st.markdown(f"""
        <div class="metric-row">
            {items_html}
        </div>
    """, unsafe_allow_html=True)


def render_position_badge(posicao: int) -> str:
    """
    Retorna o HTML de um *badge* que indica a posição no ranking.
    O próprio CSS `.position-badge` já define cores e cantos.
    """
    return f'<span class="position-badge">{posicao}°</span>'


def render_points_badge(pontos) -> str:
    """
    Renderiza o badge que indica quantos pontos foram ganhos.

    O parâmetro ``pontos`` pode ser int, float, str ou até ``None``.
    Se não for possível convertê‑lo para inteiro, a função devolve
    uma *string* vazia (nenhum badge será exibido) – evitando o
    ``TypeError`` que ocorria ao comparar string com int.
    """
    try:
        pts = int(float(pontos))
    except (TypeError, ValueError):
        return ""

    if pts == 0:
        return ""

    sinal = "+" if pts >= 0 else "-"
    return f'<span class="points-badge">{sinal}{abs(pts)} pts</span>'


def render_progress_bar(percentual: float, label: str | None = None) -> None:
    """
    Exibe uma barra de progresso estilizada.

    Args:
        percentual: Valor entre 0 e 100 (qualquer número será truncado ao intervalo permitido).
        label: Texto opcional que aparecerá acima da barra.
    """
    pct = max(0, min(100, percentual))
    barra_html = f'''
        <div class="progress-bar">
            <div class="progress-bar-fill" style="width:{pct}%"></div>
        </div>
    '''
    if label:
        barra_html = f'<div style="font-weight:bold;margin-bottom:4px;">{label}</div>' + barra_html
    st.markdown(barra_html, unsafe_allow_html=True)


def render_action_progress(actions: List[Dict[str, Any]]) -> None:
    """
    Renderiza cartões de progresso de ações gamificadas.

    **Flexibilidade de chaves** – a página *02_Colaborador.py* envia:
        - ``nome``   → nome da ação
        - ``feitas`` → quantidade já efetuada hoje
        - ``limite`` → limite diário (``None`` = ilimitado)
        - ``pontos`` → pontos ganhos por ocorrência (opcional)

    Para manter compatibilidade com a definição anterior, o componente aceita
        também as chaves ``label`` e ``progresso``.  Assim, qualquer um dos dois
        formatos funciona.

    Exemplo de lista aceita:
    ```python
    actions = [
        {"nome": "Check‑in", "feitas": 1, "limite": 1, "pontos": 10},
        {"label": "Post Instagram", "progresso": 3, "limite": 5, "pontos": 2},
    ]
    ```
    """
    for a in actions:
        raw_label = a.get("label") or a.get("nome") or ""
        chave_normalizada = raw_label.lower().replace(' ', '_')
        label = ACTION_LABELS.get(chave_normalizada,
                                 raw_label.replace('_', ' ').title())

        progresso = a.get("progresso") if a.get("progresso") is not None else a.get("feitas", 0)
        limite = a.get("limite")
        pontos = a.get("pontos")

        if limite is None:
            progresso_txt = f"{int(progresso)} / ∞"
            pct = 0
        else:
            progresso_txt = f"{int(progresso)} / {int(limite)}"
            pct = (float(progresso) / float(limite) * 100) if limite else 0

        badge_pts = render_points_badge(pontos) if pontos is not None else ""

        st.markdown(f'''
            <div class="action-progress-card">
                <div class="action-progress-row">
                    <span class="action-progress-label">{label}</span>
                    <span class="action-progress-value">{progresso_txt} {badge_pts}</span>
                </div>
                {'<div class="progress-bar"><div class="progress-bar-fill" style="width:' + str(pct) + '%"></div></div>' if limite else ''}
            </div>
        ''', unsafe_allow_html=True)


def render_leaderboard(ranking: List[Dict[str, Any]]) -> None:
    """
    Renderiza o *Leaderboard* completo.

    Cada item da lista deve conter, no mínimo:
        - ``posicao`` (int): posição no ranking
        - ``nome`` (str): nome do colaborador
        - ``pontos`` (int): pontuação total
        - ``ganho`` (int, opcional): pontos ganhos nesta ação (para exibir o badge)

    Exemplo de estrutura:
    ```python
    ranking = [
        {"posicao": 1, "nome": "Ana", "pontos": 120, "ganho": 10},
        {"posicao": 2, "nome": "Bruno", "pontos": 95},
        ...
    ]
    ```
    """
    if not ranking:
        st.info("Nenhum dado de ranking disponível.")
        return

    st.space("small")
    st.markdown('<div class="leaderboard-header">Classificação e Pontuação</div>', unsafe_allow_html=True)

    for linha in ranking:
        pos = linha.get("posicao")
        nome = linha.get("nome", "")
        pts = linha.get("pontos", 0)
        ganho = linha.get("ganho")

        badge_pos = render_position_badge(pos) if pos is not None else ""
        badge_pts = render_points_badge(ganho) if ganho is not None else ""

        linha_html = f'''
            <div class="leaderboard-row">
                <div>{badge_pos} <strong>{nome}</strong></div>
                <div>{pts} pts {badge_pts}</div>
            </div>
        '''
        st.markdown(linha_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # fecha .leaderboard-card


# ----------------------------------------------------------------------
# NOVO COMPONENTE – INFORMAÇÃO DO RANKING
# ----------------------------------------------------------------------
def render_info_ranking(titulo: str, mensagem: str) -> None:
    """
    Renderiza um card informativo *específico* para explicar como funciona
    o ranking. O visual é mais compacto que ``render_info_banner`` e
    utiliza a classe CSS ``.info-ranking-card`` definida em
    ``utils/styles.py``.

    Args:
        titulo:   Título que aparecerá em ``<h2>`` (ex.: "⚙️ Como funciona o ranking").
        mensagem: Texto já formatado em HTML/Markdown (pode conter ``<ul>``, ``<li>``, etc.).
    """

    st.markdown(f'''
        <div class="info-ranking-card">
            <h2>{titulo}</h2>
            <p>{mensagem}</p>
        </div>
    ''', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# NOVOS COMPONENTES – REGISTRO E RESUMO DE MATERIAIS
# ----------------------------------------------------------------------
def render_material_form(secrets) -> None:
    """
    Exibe **card** com formulário **para registrar material a nível de grupo**.

    Não é necessário escolher um colaborador individual; o supervisor
    informa apenas:
        • tipo do material (texto livre)
        • quantidade total recebida
        • quantidade já utilizada (ou seja, que já saiu do estoque)
    O componente captura automaticamente o ``ID_Grupo`` do supervisor
    que está logado e o envia para ``fn.registrar_material_supervisor`` (campo
    ``id_grupo`` da função backend).  O ``qnt_total`` e o ``qnt_usada``
    são gravados nas colunas “quantidade_total” e “quantidade_restante”.
    """
    st.markdown(
        '<div class="material-card"><h3>📦 Registro de Material (Grupo)</h3></div>',
        unsafe_allow_html=True,
    )

    with st.form(key="form_material_grupo", clear_on_submit=True):
        tipo_sel = st.text_input(
            "Tipo de material (ex.: “Água”, “Máscara”, “Kit de primeiros socorros”)",
            key="tipo_input"
        )

        total_qnt = st.number_input(
            "Quantidade TOTAL recebida", min_value=0, step=1, key="total_input"
        )

        usada_qnt = st.number_input(
            "Quantidade já USADA (ou seja, que já saiu do estoque)",
            min_value=0, step=1, key="usada_input"
        )

        supervisor = st.session_state.get("usuario_logado", {})
        id_grupo = supervisor.get("ID_Grupo")            # pode ser None
        nome_grupo = supervisor.get("Nome_Grupo") or f"Grupo {id_grupo}"

        submit = st.form_submit_button("Registrar entrega")

        if submit:
            ok = fn.registrar_material_supervisor(
                id_usuario=str(id_grupo) if id_grupo is not None else "DESCONHECIDO",
                nome_usuario=str(nome_grupo),
                tipo_material=tipo_sel.strip(),
                qnt_total=int(total_qnt),
                qnt_usada=int(usada_qnt),
                id_grupo=id_grupo,            # opcional – será gravado na coluna “grupo_id”
                secrets=secrets,
                error_log=st.session_state.get('error_log'),
            )
            if ok:
                st.success("Entrega registrada com sucesso!")
            else:
                st.error("Falha ao registrar. Consulte os logs.")


def render_material_summary(id_usuario: str, secrets) -> None:
    """
    Exibe, para cada tipo de material já registrado no **grupo**, um
    select‑box que permite ao supervisor indicar o nível de estoque:
    * Pouco
    * Médio
    * Muito

    Ao clicar em **“💾 Salvar nível”**, o valor escolhido é gravado
    na coluna ``nivel_material`` da aba “Materiais”.
    """
    # 1️⃣ Carregar os registros “brutos” (uma linha por tipo)
    df_raw = fn.obter_materiais_por_grupo(id_usuario=id_usuario, _secrets=secrets)

    if df_raw.empty:
        st.info("Ainda não há registros de material para este grupo.")
        return

    # 2️⃣ Definir opções de nível
    niveis = ["Pouco", "Médio", "Muito"]

    # 3️⃣ Interface linha‑a‑linha **com botão individual**
    for idx, row in df_raw.iterrows():
        with st.container(border=True):
            st.markdown(f"**Tipo:** {row['tipo_material']}")

            nivel_atual = row.get("nivel_material", "Médio")
            if nivel_atual not in niveis:
                nivel_atual = "Médio"

            # selectbox (valor guardado em session_state)
            select_key = f"nivel_{id_usuario}_{idx}"
            nivel_escolhido = st.selectbox(
                "Nível de estoque",
                niveis,
                index=niveis.index(nivel_atual),
                key=select_key
            )

            # botão “Salvar nível” para **este** material
            if st.button(
                "💾 Salvar nível",
                key=f"save_nivel_{id_usuario}_{idx}",
                help=f"Salvar nível de estoque para {row['tipo_material']}"
            ):
                ok = fn.atualizar_nivel_material_grupo(
                    id_usuario=str(id_usuario),
                    tipo_material=str(row["tipo_material"]).strip(),
                    nivel=nivel_escolhido,
                    _secrets=secrets,
                    error_log=st.session_state.get("error_log")
                )
                if ok:
                    st.success(f"Nível de **{row['tipo_material']}** atualizado para **{nivel_escolhido}**.")
                else:
                    st.error(f"Falha ao atualizar nível de **{row['tipo_material']}**.")

    # 4️⃣ Separador visual (mantém a estética)
    st.markdown("---")
    st.markdown("**📋 Níveis de estoque** (selecionar e salvar individualmente)")
