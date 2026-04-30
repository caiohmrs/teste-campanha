# =============================================================================
# CAMPANHA.PY - ARQUIVO PRINCIPAL (ENTRY POINT)
# =============================================================================
# 
# Este arquivo é apenas o ponto de entrada da aplicação.
# Toda a lógica está em:
#   - pages/_00_Login.py (Tela de login)
#   - pages/_01_Principal.py (Painel principal pós-login)
#   - utils/styles.py (Estilização CSS centralizada)
#   - funcoes.py (Funções utilitárias e conexões)
# =============================================================================


import streamlit as st
from utils.styles import inject_styles

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="COMANDO 2026",
    page_icon="🧢",
    layout="wide"
)

inject_styles()

# =============================================================================
# CONFIGURAR NAVEGAÇÃO COM PÁGINAS OCULTAS
# =============================================================================

login_page = st.Page("pages/_00_Login.py", title="Login", icon="🏠", default=True)
principal_page = st.Page("pages/_01_Principal.py", title="Principal", icon="🚀")

# Navegação com páginas ocultas da sidebar
pg = st.navigation(
    pages=[login_page, principal_page],
    position="hidden"  # ← Isso esconde o menu de navegação
)

pg.run()
# =============================================================================
# INJETAR ESTILOS CENTRALIZADOS
# =============================================================================

inject_styles()

# =============================================================================
# REDIRECIONAR PARA LOGIN
# =============================================================================

st.switch_page("pages/_00_Login.py")
