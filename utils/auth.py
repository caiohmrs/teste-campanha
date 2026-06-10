# =============================================================================
# UTILS/AUTH.PY - AUTENTICACAO GOOGLE OAUTH PARA STREAMLIT
# =============================================================================
# Fluxo OAuth manual com botao HTML customizado estilo oficial Google
# =============================================================================

import streamlit as st
import requests
import urllib.parse

SCOPES = "openid email profile"

_URL_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
_URL_TOKEN = "https://oauth2.googleapis.com/token"
_URL_USERINFO = "https://www.googleapis.com/oauth2/v2/userinfo"


def _get_client_config():
    return {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "redirect_uri": st.secrets["google_oauth"]["redirect_uri"],
    }


def exchange_code_for_token(code):
    """Troca o code do Google por um access token."""
    cfg = _get_client_config()
    payload = {
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": cfg["redirect_uri"],
        "grant_type": "authorization_code",
    }
    resp = requests.post(_URL_TOKEN, data=payload, timeout=15)
    if resp.status_code != 200:
        raise Exception(
            "Erro ao trocar code por token: {} - {}".format(resp.status_code, resp.text)
        )
    return resp.json()


def get_user_info(access_token):
    """Busca info do usuario Google pelo access token."""
    headers = {"Authorization": "Bearer {}".format(access_token)}
    resp = requests.get(_URL_USERINFO, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise Exception("Erro ao buscar user info: {}".format(resp.status_code))
    data = resp.json()
    return {
        "email": data.get("email", "").lower().strip(),
        "nome": data.get("name", ""),
        "foto": data.get("picture", ""),
        "google_id": data.get("id", ""),
    }


def login_google():
    """
    Mostra o botao de login Google e retorna info do usuario se autenticado.
    
    Returns:
        dict or None: Dicionario com dados do usuario se autenticado, None caso contrario.
    """
    # Gerar URL de autorizacao Google
    cfg = _get_client_config()
    auth_params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "online",
        "prompt": "consent",
    }
    auth_url = _URL_AUTH + "?" + urllib.parse.urlencode(auth_params)

    # Botao estilo oficial Google com SVG inline
    google_btn_html = f"""
    <div style="display:flex;justify-content:center;margin:16px 0;">
      <a href="{auth_url}" class="btn-google-login">
        <svg class="google-g-logo" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59a14.5 14.5 0 0 1 0-9.18l-7.98-6.19a24.01 24.01 0 0 0 0 21.56l7.98-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          <path fill="none" d="M0 0h48v48H0z"/>
        </svg>
        <span>Fazer login com o Google</span>
      </a>
    </div>
    """
    st.markdown(google_btn_html, unsafe_allow_html=True)

    return None
