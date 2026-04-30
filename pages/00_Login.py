# =============================================================================
# PAGES/00_🏠_LOGIN.PY - TELA DE LOGIN
# =============================================================================

import streamlit as st
import extra_streamlit_components as stx
import pandas as pd
import time
import traceback
from datetime import datetime

from funcoes import carregar_dados, get_agora_br
from utils.styles import inject_styles

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

st.set_page_config(
    page_title="COMANDO 2026 - Login",
    page_icon="🧢",
    layout="centered"
)

inject_styles()

# =============================================================================
# ESTADO E COOKIES
# =============================================================================

cookie_manager = stx.CookieManager()

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# =============================================================================
# REDIRECIONAR SE JÁ LOGADO
# =============================================================================

if st.session_state["usuario_logado"] is not None:
    st.switch_page("pages/01_Principal.py")

# =============================================================================
# TELA DE LOGIN
# =============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])

with col_l2:
    st.markdown(f"""
        <h1 style='text-align: center; font-size: 4rem; line-height: 0.9; margin-bottom: 20px; margin-top: -100px'>
            Max Maciel<br><span style='color: var(--cor-secundaria);'>🧢 2026</span>
        </h1>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(f"""
            <div style='background-color: var(--cor-primaria); padding: 15px; border: 4px solid var(--cor-texto); box-shadow: 10px 10px 0px var(--cor-texto); text-align: center;'>
                <h2 style='margin-top: 0; font-size: 1.5rem; font-family: "Archivo Black", sans-serif; font-style: italic; text-transform: uppercase; color: var(--cor-texto);'>
                    Faça seu login abaixo:
                </h2>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

        email_input = st.text_input(
            "ID DE USUÁRIO (E-MAIL)", 
            placeholder="seu@email.com",
            label_visibility="collapsed"
        )

        if st.button("ENTRAR NO PAINEL", width='stretch', type="primary"):
            with st.spinner("VALIDANDO..."):
                try:
                    df_usuarios = carregar_dados(
                        "Usuarios", 
                        st.secrets["planilha"]["id"], 
                        st.session_state.get('error_log')
                    )
                    
                    if df_usuarios is not None:
                        user_match = df_usuarios[
                            df_usuarios['ID_Usuario'].str.lower() == email_input.lower().strip()
                        ]
                        
                        if not user_match.empty:
                            st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                            cookie_manager.set(
                                "comando2026_user_id", 
                                email_input.lower().strip(),
                                key="set_user_cookie"
                            )
                            st.rerun()
                        else:
                            st.error("❌ ID NÃO ENCONTRADO")
                    else:
                        st.error("❌ ERRO AO CARREGAR DADOS")
                        
                except Exception as e:
                    st.session_state['error_log'].append({
                        'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                        'erro': str(e),
                        'funcao': 'login.validar_usuario',
                        'traceback': traceback.format_exc(),
                        'tipo': type(e).__name__
                    })
                    st.error(f"❌ ERRO: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Primeiro acesso? Solicite seu ID ao seu supervisor.")
