# =============================================================================
# CAMPANHA.PY - ARQUIVO PRINCIPAL (ENTRY POINT)
# =============================================================================
# 
# Este arquivo é apenas o ponto de entrada da aplicação.
# Toda a lógica está em:
#   - pages/00_Login.py (Tela de login)
#   - pages/01_Principal.py (Painel principal pós-login)
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
                                                                                                  

# =============================================================================
# INJETAR ESTILOS CENTRALIZADOS
# =============================================================================

inject_styles()

# =============================================================================
# REDIRECIONAR PARA LOGIN
# =============================================================================

st.switch_page("pages/00_Login.py")
