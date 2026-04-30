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
