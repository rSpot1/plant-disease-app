import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import requests
import os
from google.auth.transport.requests import Request

def get_google_auth_flow():
    """Crée et retourne un objet Flow pour l'authentification Google OAuth2."""
    if "GOOGLE_CLIENT_ID" not in st.secrets or "GOOGLE_CLIENT_SECRET" not in st.secrets:
        st.error("Les secrets GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET ne sont pas configurés.")
        st.stop()

    redirect_uri = st.secrets.get("REDIRECT_URI")

    # CORRECTION ICI : Utiliser from_client_config au lieu de from_client_secrets_dict
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ],
        redirect_uri=redirect_uri,
    )

def display_login_button():
    """Affiche le bouton de connexion et retourne l'URL d'autorisation."""
    flow = get_google_auth_flow()
    auth_url, _ = flow.authorization_url(prompt="consent")
    
    st.markdown(f"""
    <a href="{auth_url}" target="_self" style="display: inline-block; padding: 0.5rem 1rem; background-color: #4285F4; color: white; border-radius: 0.25rem; text-decoration: none;">
        Se connecter avec Google
    </a>
    """, unsafe_allow_html=True)

def handle_auth_callback():
    """Gère le callback après l'authentification et stocke les informations de l'utilisateur."""
    code = st.query_params.get("code")
    if code and 'user_info' not in st.session_state:
        try:
            flow = get_google_auth_flow()
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # CORRECTION ICI : Utiliser un objet Request approprié
            request = Request()
            id_info = id_token.verify_oauth2_token(
                id_token=credentials.id_token,
                request=request,
                audience=st.secrets["GOOGLE_CLIENT_ID"],
            )
            
            st.session_state.user_info = id_info
            st.rerun() # Pour nettoyer l'URL et afficher l'état connecté
        except Exception as e:
            st.error(f"Erreur lors de l'authentification : {e}")
            st.stop()
