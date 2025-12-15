import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import os
from google.auth.transport.requests import Request
import urllib.parse

def get_google_auth_flow():
    """Crée et retourne un objet Flow pour l'authentification Google OAuth2."""
    if "GOOGLE_CLIENT_ID" not in st.secrets or "GOOGLE_CLIENT_SECRET" not in st.secrets:
        st.error("Les secrets GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET ne sont pas configurés.")
        st.stop()

    # IMPORTANT : Détection automatique de l'environnement
    if os.environ.get("STREAMLIT_SHARING") == "True" or os.environ.get("STREAMLIT_SERVER"):
        # En production sur Streamlit Cloud
        redirect_uri = f"https://{os.environ.get('STREAMLIT_APP_NAME', 'share')}.streamlit.app"
    else:
        # En développement local
        redirect_uri = "http://localhost:8501"
    
    st.write(f"🌐 Redirect URI utilisé : {redirect_uri}")  # Pour debug

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
    try:
        flow = get_google_auth_flow()
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        
        # Utiliser st.link_button pour une meilleure compatibilité
        if st.button("🔐 Se connecter avec Google", type="primary", use_container_width=True):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erreur de configuration : {e}")

def handle_auth_callback():
    """Gère le callback après l'authentification et stocke les informations de l'utilisateur."""
    code = st.query_params.get("code")
    if code and 'user_info' not in st.session_state:
        try:
            with st.spinner("Authentification en cours..."):
                flow = get_google_auth_flow()
                flow.fetch_token(code=code)
                credentials = flow.credentials
                
                # Vérifier le token
                request = Request()
                id_info = id_token.verify_oauth2_token(
                    id_token=credentials.id_token,
                    request=request,
                    audience=st.secrets["GOOGLE_CLIENT_ID"],
                )
                
                # Stocker les informations utilisateur
                st.session_state.user_info = {
                    'email': id_info.get('email'),
                    'name': id_info.get('name'),
                    'picture': id_info.get('picture'),
                    'token': credentials.token
                }
                
                # Nettoyer l'URL
                st.query_params.clear()
                st.rerun()
                
        except Exception as e:
            st.error(f"Erreur d'authentification : {str(e)}")
            st.write("Code reçu:", code[:50] if code else "Aucun")
