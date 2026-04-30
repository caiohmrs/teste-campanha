# =============================================================================
# STYLES.PY - ESTILIZAÇÃO CENTRALIZADA "COMANDO 2026"
# =============================================================================
# 
# 🎨 COMO MUDAR AS CORES DO TEMA:
#   Edite o dicionário CORES abaixo e recarregue o app.
# 
# 🧱 COMO MUDAR O ESTILO NEO-BRUTALISTA:
#   Edite o dicionário ESTILO abaixo para controlar bordas, sombras, etc.
# 
# =============================================================================

# =============================================================================
# VARIÁVEIS DE CORES (EDITAR AQUI PARA MUDAR O TEMA)
# =============================================================================

CORES = {
    'primaria': '#FFEB00',      # Amarelo (sidebar, cards, destaque)
    'secundaria': '#E20613',    # Vermelho (botões, ações, destaques)
    'texto': '#1D1D1B',         # Preto (bordas, texto principal)
    'fundo': '#F4F4F4',         # Cinza claro (fundos secundários)
    'branco': '#FFFFFF',        # Branco (fundos de cards, inputs)
    'gradiente_inicio': '#E9ECEF',
    'gradiente_fim': '#ADB5BD',
}

# =============================================================================
# VARIÁVEIS DE ESTILO NEO-BRUTALISTA (EDITAR AQUI PARA MUDAR O VISUAL)
# =============================================================================

ESTILO = {
    'borda_largura': '3px',       # Largura das bordas (1px a 5px)
    'borda_estilo': 'solid',      # Estilo: solid, dashed, dotted
    'sombra_offset_x': '4px',     # Sombra horizontal
    'sombra_offset_y': '4px',     # Sombra vertical
    'sombra_blur': '0px',         # Blur da sombra (0px = sólido)
    'border_radius': '0px',       # Arredondamento (0px = quadrado)
    'fonte_titulo': '"Archivo Black", sans-serif',
    'fonte_texto': '"Roboto", sans-serif',
}

# =============================================================================
# CSS COMPLETO
# =============================================================================

def get_css():
    """
    Retorna todo o CSS da aplicação em uma única string.
    
    Returns:
        str: String contendo todo o CSS formatado dentro de tags <style>.
    """
    
    return f"""
    <style>
        /* 0. CONFIGURAÇÕES TÉCNICAS E FONTES */
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto:wght@400;700&display=swap');

        :root {{
            color-scheme: light !important;
            
            /* Variáveis CSS para cores */
            --cor-primaria: {CORES['primaria']};
            --cor-secundaria: {CORES['secundaria']};
            --cor-texto: {CORES['texto']};
            --cor-fundo: {CORES['fundo']};
            --cor-branco: {CORES['branco']};
            --gradiente-inicio: {CORES['gradiente_inicio']};
            --gradiente-fim: {CORES['gradiente_fim']};
            
            /* Variáveis CSS para estilo neo-brutalista */
            --borda-largura: {ESTILO['borda_largura']};
            --borda-estilo: {ESTILO['borda_estilo']};
            --sombra-offset-x: {ESTILO['sombra_offset_x']};
            --sombra-offset-y: {ESTILO['sombra_offset_y']};
            --sombra-blur: {ESTILO['sombra_blur']};
            --border-radius: {ESTILO['border_radius']};
            --fonte-titulo: {ESTILO['fonte_titulo']};
            --fonte-texto: {ESTILO['fonte_texto']};
        }}

        /* 1. CONFIGURAÇÕES GERAIS DA APP */
        [data-testid="stVerticalBlock"] > div {{
            width: 100%;
        }}

        .stApp {{
            background: linear-gradient(135deg, var(--gradiente-inicio) 0%, var(--gradiente-fim) 100%) !important;
            background-attachment: fixed !important;
            color: var(--cor-texto) !important;
            font-family: var(--fonte-texto), sans-serif;
        }}

        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"], 
        [data-testid="stVerticalBlock"],
        [data-testid="stMainBlockContainer"] {{
            background-color: transparent !important;
        }}

        /* 2. SIDEBAR */
        section[data-testid="stSidebar"] {{
            background-color: var(--cor-primaria) !important;
            border-right: var(--borda-largura) var(--borda-estilo) var(--cor-texto) !important;
        }}

        /* 3. TIPOGRAFIA (HEADINGS) */
        h1, h2, h3 {{                                                                                      
            font-family: var(--fonte-titulo) !important;                                                   
            text-transform: uppercase;                                                                     
            font-style: italic;                                                                            
            color: var(--cor-texto) !important;                                                            
            text-align: center;  
        }}

        /* 4. BOTÕES */
        .stButton > button, 
        div[data-testid="stPopover"] > button {{
            background-color: var(--cor-secundaria) !important;
            color: var(--cor-branco) !important;
            font-family: var(--fonte-titulo) !important;
            border: var(--borda-largura) var(--borda-estilo) var(--cor-texto) !important;
            border-radius: var(--border-radius) !important;
            text-transform: uppercase !important;
            box-shadow: var(--sombra-offset-x) var(--sombra-offset-y) var(--sombra-blur) var(--cor-texto) !important;
            width: 100% !important;
            min-height: 3.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        /* 5. TABS */
        div[data-baseweb="tab-list"] {{
            gap: 0px !important;
            background-color: transparent !important;
            padding: 10px 0 !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }}

        button[data-baseweb="tab"] {{
            background-color: var(--cor-primaria) !important;
            border: var(--borda-largura) var(--borda-estilo) var(--cor-texto) !important;
            border-radius: var(--border-radius) !important;
            padding: 10px 20px !important;
            font-family: var(--fonte-titulo), sans-serif !important;
            text-transform: uppercase !important;
            font-style: italic !important;
            color: var(--cor-texto) !important;
            box-shadow: var(--sombra-offset-x) var(--sombra-offset-y) var(--sombra-blur) var(--cor-texto) !important;
            transition: 0.2s !important;
            margin: 0 6px 10px 6px !important;
            transform: none !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: var(--cor-secundaria) !important;
            color: var(--cor-branco) !important;
            box-shadow: var(--sombra-offset-x) var(--sombra-offset-y) var(--sombra-blur) var(--cor-texto) !important;
            transform: none !important;
        }}

        button[data-baseweb="tab"][aria-selected="false"]:hover {{
            transform: translate(-2px, -2px) !important;
            box-shadow: calc(var(--sombra-offset-x) + 2px) calc(var(--sombra-offset-y) + 2px) var(--sombra-blur) var(--cor-texto) !important;
        }}

        div[data-baseweb="tab-highlight"] {{
            display: none !important;
        }}

        button[data-baseweb="tab"] p {{
            font-size: 0.85rem !important;
            font-weight: bold !important;
            color: inherit !important;
            margin: 0 !important;
        }}

        /* 6. EXPANDERS E BORDAS */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="border"] {{
            border: var(--borda-largura) var(--borda-estilo) var(--cor-texto) !important;
            background-color: var(--cor-fundo) !important;
            box-shadow: calc(var(--sombra-offset-x) + 2px) calc(var(--sombra-offset-y) + 2px) var(--sombra-blur) var(--cor-primaria) !important;
        }}

        /* 7. INPUTS DE TEXTO */
        .stTextInput input {{
            border: var(--borda-largura) var(--borda-estilo) var(--cor-texto) !important;
            text-align: center !important;
            background-color: var(--cor-branco) !important;
            border-radius: var(--border-radius) !important;
        }}

        /* 8. FOOTER E DECORAÇÕES */
        footer {{
            display: none !important;
            visibility: hidden !important;
        }}

        div[data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stHeaderActionElements"], .stDeployButton {{
            display: none !important;
            visibility: hidden !important;
        }}

        header[data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0) !important;
            color: var(--cor-texto) !important;
        }}

        /* 9. CONTAINER PRINCIPAL */
        .block-container {{
            padding-top: 2rem !important;
        }}

        /* 10. RESPONSIVIDADE (MOBILE) */
        @media (max-width: 768px) {{
            button[data-baseweb="tab"] {{
                font-size: 0.7rem !important;
                padding: 8px 10px !important;
            }}
        }}

        /* 11. BOTÃO DE FECHAR MODAL */
        button[aria-label="Close"] {{
            display: none !important;
        }}

        /* =====================================================================
           COMPONENTES REUTILIZÁVEIS (CSS MOVIDO DAS PÁGINAS)
           ===================================================================== */

        /* 12. LOGIN HEADER */
        .login-header {{
            text-align: center;
            font-size: 4rem;
            line-height: 0.9;
            margin-bottom: 20px;
            margin-top: -100px;
        }}

        .login-header-subtitle {{
            color: var(--cor-secundaria);
        }}

        /* 13. LOGIN BOX */
        .login-box {{
            background-color: var(--cor-primaria);
            padding: 15px;
            border: 4px solid var(--cor-texto);
            box-shadow: 10px 10px 0px var(--cor-texto);
            text-align: center;
        }}

        .login-box h2 {{
            margin-top: 0;
            font-size: 1.5rem;
            font-family: "Archivo Black", sans-serif;
            font-style: italic;
            text-transform: uppercase;
            color: var(--cor-texto);
        }}

        /* 14. WELCOME BANNER */
        .welcome-banner {{
            background-color: var(--cor-primaria);
            padding: 15px;
            border: 4px solid var(--cor-texto);
            box-shadow: 8px 8px 0px var(--cor-texto);
            text-align: center;
            width: 90%;
            margin: 10px auto 25px auto;
        }}

        .welcome-banner-title {{
            margin: 0;
            font-size: 1.5rem;
            font-family: "Archivo Black", sans-serif;
            font-style: italic;
            color: var(--cor-texto);
            line-height: 1;
        }}

        .welcome-banner-name {{
            margin: 0;
            font-size: 2.2rem;
            font-family: "Archivo Black", sans-serif;
            font-style: italic;
            text-transform: uppercase;
            color: var(--cor-secundaria);
            line-height: 1.1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
            margin-top: -30px;
        }}

        /* 15. STATUS BAR */
        .status-bar {{
            background-color: var(--cor-primaria);
            border-top: 2px solid var(--cor-texto);
            border-bottom: 2px solid var(--cor-texto);
            padding: 6px 0;
            margin: 10px 0 25px 0;
            display: flex;
            justify-content: center;
            gap: 40px;
            font-family: "Archivo Black", sans-serif;
            text-transform: uppercase;
            font-style: italic;
        }}

        .status-bar-item {{
            color: var(--cor-texto);
            font-size: 0.9rem;
        }}

        .status-bar-dot {{
            color: var(--cor-secundaria);
        }}

        /* 16. SECTION HEADER */
        .section-header {{
            background-color: var(--cor-primaria);
            padding: 15px;
            border: 4px solid var(--cor-texto);
            box-shadow: 8px 8px 0px var(--cor-texto);
            text-align: center;
            margin-bottom: 25px;
        }}

        .section-header h2 {{
            margin: 0;
            font-size: 1.8rem;
            font-style: italic;
            color: var(--cor-texto);
        }}

        /* 17. MODAL HEADER */
        .modal-header {{
            background-color: var(--cor-primaria);
            padding: 15px;
            border: 3px solid var(--cor-texto);
            text-align: center;
            margin-bottom: 20px;
        }}

        .modal-header h2 {{
            margin: 0;
            font-size: 1.5rem;
            font-style: italic;
            color: var(--cor-texto);
        }}

        /* 18. INFO BANNER (MENSAGEM DO DIA) */
        .info-banner {{
            background-color: var(--cor-primaria);
            padding: 40px 20px;
            border: 5px solid var(--cor-texto);
            box-shadow: 10px 10px 0px var(--cor-texto);
            text-align: center;
            margin-top: 20px;
        }}

        .info-banner h1 {{
            font-family: "Archivo Black", sans-serif;
            font-style: italic;
            color: var(--cor-texto);
            font-size: 2.5rem;
        }}

        .info-banner-subtitle {{
            color: var(--cor-secundaria);
        }}

        .info-banner hr {{
            border: 2px solid var(--cor-texto);
            margin: 20px 0;
        }}

        .info-banner p {{
            font-size: 1.4rem;
            font-weight: bold;
            color: var(--cor-texto);
            line-height: 1.4;
        }}

        /* 19. TICKER (ADMIN) */
        .ticker-container {{
            width: 100%;
            overflow: hidden;
            background: var(--cor-primaria);
            border-top: 3px solid var(--cor-texto);
            border-bottom: 3px solid var(--cor-texto);
            padding: 8px 0;
            margin-bottom: 25px;
            white-space: nowrap;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        }}

        .ticker-content {{
            display: inline-block;
            animation: scroll 45s linear infinite;
            font-family: 'Archivo Black', sans-serif;
            font-size: 0.9rem;
            color: var(--cor-texto);
            font-style: italic;
            text-transform: uppercase;
        }}

        .ticker-content:hover {{
            animation-play-state: paused;
        }}

        @keyframes scroll {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        /* 20. TEAM CARD (SUPERVISOR/ADMIN) */
        .team-card {{
            background-color: var(--cor-branco);
            border: 4px solid var(--cor-texto);
            box-shadow: 6px 6px 0px var(--cor-texto);
            padding: 20px;
            margin-bottom: 12px;
        }}

        .team-card-header {{
            border-bottom: 3px solid var(--cor-texto);
            padding-bottom: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .team-card-name {{
            margin: 0;
            font-family: "Archivo Black", sans-serif;
            font-size: 1.5rem;
            color: var(--cor-secundaria);
            text-transform: uppercase;
        }}

        .team-card-macro {{
            font-size: 0.8rem;
            color: #666;
            font-weight: bold;
        }}

        .team-card-badge {{
            background-color: var(--cor-primaria);
            border: 2px solid var(--cor-texto);
            padding: 4px 10px;
            font-family: "Archivo Black", sans-serif;
            font-size: 0.8rem;
        }}

        .team-card-metric {{
            flex: 1;
            background-color: var(--cor-fundo);
            border: 2px solid var(--cor-texto);
            padding: 12px;
            text-align: center;
        }}

        .team-card-metric-label {{
            font-family: "Archivo Black", sans-serif;
            font-size: 0.85rem;
            color: #666;
        }}

        .team-card-metric-value {{
            font-family: "Archivo Black", sans-serif;
            font-size: 2.2rem;
            color: var(--cor-texto);
            line-height: 1;
            margin-top: 5px;
        }}

        /* 21. METRIC CARD */
        .metric-card {{
            background: var(--cor-branco);
            border: 4px solid var(--cor-texto);
            padding: 20px;
            text-align: center;
            box-shadow: 6px 6px 0px var(--cor-texto);
        }}

        .metric-card-label {{
            font-family: 'Archivo Black';
            font-size: 0.9rem;
            color: #666;
        }}

        .metric-card-value {{
            font-family: 'Archivo Black';
            font-size: 3rem;
            color: var(--cor-texto);
            line-height: 1;
            margin-top: 10px;
        }}

        .metric-card-value-secondary {{
            color: var(--cor-secundaria);
        }}

        /* 22. SUPPORT PANEL (SUPORTE) */
        .support-panel {{
            background-color: var(--cor-secundaria);
            padding: 20px;
            border: 4px solid var(--cor-texto);
            box-shadow: 8px 8px 0px var(--cor-texto);
            text-align: center;
            margin-bottom: 25px;
        }}

        .support-panel h1 {{
            margin: 0;
            font-family: "Archivo Black", sans-serif;
            font-style: italic;
            color: var(--cor-branco);
            font-size: 2.5rem;
        }}

        .support-panel p {{
            margin: 10px 0 0 0;
            color: var(--cor-primaria);
            font-weight: bold;
        }}

        /* 23. DIAGNOSTIC CARD */
        .diagnostic-card {{
            border: 3px solid var(--cor-texto);
            padding: 15px;
            text-align: center;
            box-shadow: 4px 4px 0px var(--cor-texto);
        }}

        .diagnostic-card h3 {{
            margin: 0;
            color: var(--cor-texto);
        }}

        .diagnostic-card-status {{
            font-size: 2rem;
            margin: 10px 0;
        }}

        .diagnostic-card-msg {{
            font-size: 0.8rem;
            margin: 0;
            color: var(--cor-texto);
        }}

        /* 24. LOG ENTRY */
        .log-entry {{
            background-color: var(--cor-fundo);
            border: 2px solid var(--cor-texto);
            padding: 10px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 3px 3px 0px var(--cor-texto);
        }}

        .log-entry-action {{
            font-family: Archivo Black;
            font-size: 0.8rem;
        }}

        .log-entry-time {{
            font-size: 0.7rem;
            color: #666;
            font-weight: bold;
        }}

        .log-entry-badge {{
            background-color: var(--cor-primaria);
            border: 1px solid #000;
            padding: 1px 4px;
            font-size: 0.5rem;
            margin-left: 8px;
        }}

        .log-entry-map-btn {{
            background-color: var(--cor-secundaria);
            color: #FFF;
            padding: 3px 6px;
            border: 1px solid #000;
            font-size: 0.5rem;
            text-decoration: none;
            font-family: Archivo Black;
        }}

        /* 25. CONTRACT CARD */
        .contract-card {{
            border: 1px solid #ddd;
            padding: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .contract-card-name {{
            font-size: 0.9rem;
            font-weight: bold;
            color: var(--cor-texto);
        }}

        .contract-card-btn {{
            background-color: #25D366;
            color: #FFFFFF;
            font-size: 0.7rem;
            padding: 4px 10px;
            border: 2px solid var(--cor-texto);
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
        }}

        /* 26. ACTION LINK BUTTON */
        .action-link-btn {{
            background-color: var(--cor-texto);
            color: var(--cor-primaria);
            text-align: center;
            padding: 10px;
            border: 2px solid var(--cor-primaria);
            font-weight: bold;
            font-size: 0.8rem;
            text-decoration: none;
            display: block;
        }}

        /* 27. SMALL METRIC ROW */
        .metric-row {{
            display: flex;
            justify-content: space-between;
            gap: 5px;
            width: 100%;
            margin-bottom: 15px;
        }}

        .metric-row-item {{
            flex: 1;
            background: var(--cor-branco);
            border: 2px solid var(--cor-texto);
            box-shadow: 3px 3px 0px var(--cor-texto);
            text-align: center;
            padding: 5px;
        }}

        .metric-row-label {{
            margin: 0;
            font-size: 0.6rem;
            font-family: 'Archivo Black';
            color: #666;
        }}

        .metric-row-value {{
            margin: 0;
            font-size: 1.2rem;
            font-family: 'Archivo Black';
            color: var(--cor-texto);
        }}

        .metric-row-value-secondary {{
            color: var(--cor-secundaria);
        }}
    </style>
    """


def inject_styles():
    """
    Injeta o CSS na aplicação Streamlit.
    
    Esta função deve ser chamada uma vez no início da aplicação,
    logo após st.set_page_config().
    
    Example:
        >>> import streamlit as st
        >>> from utils.styles import inject_styles
        >>> st.set_page_config(page_title="Minha App")
        >>> inject_styles()
    """
    import streamlit as st
    st.markdown(get_css(), unsafe_allow_html=True)
    st.markdown('<meta name="color-scheme" content="light">', unsafe_allow_html=True)
