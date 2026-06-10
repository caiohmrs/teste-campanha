# =============================================================================
# CAMPANHA.PY - ARQUIVO PRINCIPAL (ENTRY POINT)
# =============================================================================
#
# Este arquivo e o ponto de entrada da aplicacao.
# Toda a logica esta em:
#   - pages/00_Login.py (Tela de login)
#   - pages/01_Principal.py (Painel principal pos-login)
#   - utils/styles.py (Estilizacao CSS centralizada)
#   - funcoes.py (Funcoes utilitarias e conexoes)
#
# =============================================================================

import streamlit as st
from utils.styles import inject_styles

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================

st.set_page_config(
    page_title="COMANDO 2026",
    page_icon="",
    layout="wide"
)

inject_styles()

# =============================================================================
# INICIALIZAR ESTADO
# =============================================================================

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []

# =============================================================================
# TRATAR CALLBACK DO GOOGLE OAUTH
# Se o Google redirecionou com ?code=..., processar aqui
# =============================================================================

query_params = st.query_params
if "code" in query_params:
    from utils.auth import exchange_code_for_token, get_user_info
    from funcoes import carregar_dados

    code = query_params["code"]

    try:
        # Trocar code por token
        token_data = exchange_code_for_token(code)
        access_token = token_data["access_token"]

        # Buscar info do usuario
        user_info = get_user_info(access_token)
        email = user_info["email"]

        # Verificar se usuario existe na planilha
        df_usuarios = carregar_dados(
            "Usuarios",
            st.secrets["planilha"]["id"],
            st.session_state.get("error_log")
        )

        if df_usuarios is not None:
            user_match = df_usuarios[
                df_usuarios["ID_Usuario"].str.lower() == email
            ]

            if not user_match.empty:
                # Login bem-sucedido
                st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                st.session_state["google_credentials"] = {
                    "token": access_token,
                    "refresh_token": token_data.get("refresh_token"),
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            else:
                st.session_state["_oauth_error"] = "E-MAIL NAO CADASTRADO. Solicite acesso ao supervisor."
        else:
            st.session_state["_oauth_error"] = "ERRO AO CARREGAR DADOS. Tente novamente."

    except Exception as e:
        st.session_state["_oauth_error"] = "Erro na autenticacao: {}".format(str(e))

    # Limpar query params
    st.query_params.clear()

# =============================================================================
# REDIRECIONAR
# =============================================================================

if st.session_state.get("usuario_logado") is None:
    st.switch_page("pages/00_Login.py")
else:
    st.switch_page("pages/01_Principal.py")
