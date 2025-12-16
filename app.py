import streamlit as st
from PIL import Image
import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import io
import base64
import requests
from inference import predict, CLASS_NAMES_TRANSLATION, CLASSES
import google.generativeai as genai
from auth import display_login_button, handle_auth_callback
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation

# Configuration de la page
st.set_page_config(
    page_title="PhytoSavior",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration Gemini
def init_gemini():
    """Initialise l'API Gemini"""
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            return True
        else:
            st.warning("Clé API Gemini non configurée")
            return False
    except Exception as e:
        st.warning(f"Erreur d'initialisation Gemini: {str(e)}")
        return False

def validate_plant_image(image):
    """Valide si l'image contient une feuille de plante avec Gemini 2.5 Flash"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Convertir l'image PIL en bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Prompt de validation strict
        prompt = """Analysez cette image. Répondez uniquement par 'OUI' si toutes ces conditions sont remplies :
        1. L'image montre clairement une feuille de plante ou des feuilles de plante
        2. La feuille/plante est le sujet principal de l'image
        3. L'image est suffisamment claire pour voir les détails de la feuille
        
        Si ce n'est pas clairement une feuille de plante, répondez 'NON'.
        Répondez uniquement par 'OUI' ou 'NON', sans aucun autre texte."""
        
        # Créer le contenu avec l'image
        image_part = {
            "mime_type": "image/jpeg",
            "data": img_bytes
        }
        
        response = model.generate_content([prompt, image_part])
        result = response.text.strip().upper()
        
        return "OUI" in result
    except Exception as e:
        #st.warning(f"Erreur lors de la validation de l'image: {str(e)}")
        return True  # En cas d'erreur, on laisse passer

def get_plant_recommendation(disease_label, confidence, plant_name=None, condition=None):
    """Obtenir des recommandations de traitement avec Gemini 2.5 Flash"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Préparer les informations météo pour le prompt
        weather_context = ""
        if 'weather_data' in st.session_state:
            temp = st.session_state.weather_data['temperature']
            humidity = st.session_state.weather_data['humidity']
            weather_context = f"""
Conditions météo actuelles :
- Température : {temp}°C
- Humidité relative : {humidity}%

IMPORTANT : Adaptez vos recommandations à ces conditions météorologiques.
Par exemple :
- Si l'humidité est élevée ({humidity}%), suggérez des traitements qui fonctionnent bien en conditions humides
- Si la température est {temp}°C, recommandez des produits adaptés à cette plage de température
- Indiquez si les conditions actuelles favorisent la propagation de la maladie diagnostiquée
"""

        # Préparer le prompt amélioré avec contexte météo
        prompt = f"""En tant qu'expert en phytopathologie, fournissez des recommandations précises et pratiques adaptées aux conditions actuelles.

DIAGNOSTIC : {disease_label}
CONFIANCE DU DIAGNOSTIC : {confidence*100:.1f}%
PLANTE CONCERNÉE : {plant_name if plant_name else 'Non spécifiée'}
CONDITION IDENTIFIÉE : {condition if condition else 'Non spécifiée'}

{weather_context}

Fournissez une réponse structurée et adaptée aux conditions avec :
1. TITRE : Un titre court décrivant le problème spécifique
2. DESCRIPTION : Brève explication de la maladie/condition (1-2 phrases)
3. ÉVALUATION DES CONDITIONS : Comment les conditions météo actuelles affectent cette maladie
4. TRAITEMENTS RECOMMANDÉS : Liste concrète de 1-2 traitements adaptés aux conditions actuelles
5. MESURES PRÉVENTIVES : 2 actions préventives spécifiques
6. SURVEILLANCE : Conseils de surveillance tenant compte des conditions météo

Utilisez un langage simple, technique mais accessible aux agriculteurs.
Soyez spécifique sur l'adaptation des traitements aux conditions météorologiques actuelles.
Ne pas utiliser de markdown (#, **, *, etc.) - utilisez uniquement du texte simple avec des retours à la ligne."""

        response = model.generate_content(prompt)
        
        # Nettoyer la réponse
        clean_text = response.text
        # Supprimer tout markdown potentiel
        markdown_chars = ['#', '*', '`', '~', '|', '>', '[', ']', '{', '}', '_']
        for char in markdown_chars:
            clean_text = clean_text.replace(char, '')
        
        # Nettoyer les espaces multiples
        import re
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        
        return clean_text.strip()
    except Exception as e:
        return f"Recommandations non disponibles pour le moment..."

# Style CSS personnalisé (épuré)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e6b3a;
        text-align: left;
        margin-bottom: 0.5rem;
        padding-top: 1rem;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #5f6368;
        text-align: left;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
    }
    
    .result-card {
        background: linear-gradient(135deg, #f8fff9 0%, #f0f9f3 100%);
        border-left: 4px solid #2e8b57;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    
    .recommendation-card {
        background-color: #f8f9ff;
        border-left: 4px solid #4285f4;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        line-height: 1.7;
        white-space: pre-line;
        font-size: 0.95rem;
    }
    
    .warning-card {
        background-color: #fff3e0;
        border-left: 4px solid #f57c00;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #f0f7ff;
        border-left: 4px solid #4285f4;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #1e6b3a;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #155d31;
        box-shadow: 0 4px 12px rgba(30, 107, 58, 0.2);
    }
    
    .camera-button {
        background-color: #4285f4 !important;
    }
    
    .camera-button:hover {
        background-color: #3367d6 !important;
    }
    
    .history-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        border-radius: 6px;
        border-left: 3px solid #1e6b3a;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e6b3a;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #5f6368;
    }
    
    .confidence-high {
        color: #34a853;
        font-weight: 600;
    }
    
    .confidence-medium {
        color: #fbbc05;
        font-weight: 600;
    }
    
    .confidence-low {
        color: #ea4335;
        font-weight: 600
    }
    
    .recommendation-section {
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e0e0e0;
    }
    
    .user-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #1e6b3a;
    }
    
    .user-info {
        flex: 1;
    }
    
    .user-name {
        font-weight: 600;
        color: #1e6b3a;
        margin: 0;
    }
    
    .user-email {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

def get_weather_data():
    """Récupère les données météo."""
    if 'user_location' in st.session_state:
        lat = st.session_state.user_location['latitude']
        lon = st.session_state.user_location['longitude']
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        try:
            response = requests.get(url)
            data = response.json()
            if 'current' in data:
                st.session_state.weather_data = {
                    "temperature": data['current']['temperature_2m'],
                    "humidity": data['current']['relative_humidity_2m']
                }
        except Exception as e:
            st.warning(f"Impossible de récupérer les données météo: {e}")

# Initialisation Firebase
def init_firebase():
    """Initialise la connexion à Firebase"""
    try:
        if 'firebase_initialized' not in st.session_state:
            firebase_config = {
                "type": os.environ.get("FIREBASE_TYPE"),
                "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
                "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
                "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_CERT_URL"),
                "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_CERT_URL")
            }
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                st.session_state.firebase_initialized = True
            
        return firestore.client()
    except Exception as e:
        st.warning(f"Firebase non configuré: {str(e)}")
        return None

# Sauvegarde dans Firebase
def save_to_firebase(db, label, confidence, image_size=None, plant_name=None, condition=None):
    """Sauvegarde les résultats dans Firebase"""
    try:
        if db is None or 'user_info' not in st.session_state:
            return False
            
        prediction_data = {
            "user_email": st.session_state.user_info['email'],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "date": datetime.now().isoformat(),
            "disease_label": label,
            "confidence": round(confidence * 100, 2),
            "image_size": image_size,
            "plant_name": plant_name,
            "condition": condition
        }

        if 'weather_data' in st.session_state:
            prediction_data['temperature'] = st.session_state.weather_data['temperature']
            prediction_data['humidity'] = st.session_state.weather_data['humidity']
        
        if 'user_location' in st.session_state:
            prediction_data['latitude'] = st.session_state.user_location['latitude']
            prediction_data['longitude'] = st.session_state.user_location['longitude']

        db.collection('predictions').add(prediction_data)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
        return False

# Récupération de l'historique
def get_history(db, limit=10):
    """Récupère l'historique des prédictions pour l'utilisateur connecté."""
    try:
        if db is None or 'user_info' not in st.session_state:
            return []
            
        user_email = st.session_state.user_info['email']
        predictions_ref = db.collection('predictions').where('user_email', '==', user_email)
        docs = predictions_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            history.append(data)
        
        return history
    except Exception as e:
        st.warning(f"Impossible de charger l'historique: {str(e)}")
        return []

def get_total_predictions(db):
    """Compte le nombre total de prédictions pour l'utilisateur connecté."""
    try:
        if db is None or 'user_info' not in st.session_state:
            return 0
        
        user_email = st.session_state.user_info['email']
        count_query = db.collection('predictions').where('user_email', '==', user_email).count()
        result = count_query.get()
        
        if result and result[0]:
            return result[0][0].value
        return 0
    except Exception as e:
        st.warning(f"Impossible de compter les prédictions: {str(e)}")
        return 0

# Fonction pour extraire les informations de la plante
def extract_plant_info(label):
    """Extrait le nom de la plante et l'état du label"""
    plant_name = "Non spécifié"
    condition = "Non spécifié"
    
    # Chercher dans les labels originaux
    for original_label in CLASSES:
        if CLASS_NAMES_TRANSLATION.get(original_label) == label:
            if "___" in original_label:
                parts = original_label.split("___")
                if len(parts) == 2:
                    plant_name = parts[0].replace("_", " ").title()
                    condition = parts[1].replace("_", " ").title()
            break
    
    return plant_name, condition

def clear_analysis_state():
    """Nettoie les résultats d'analyse précédents du session_state."""
    if 'last_analysis' in st.session_state:
        del st.session_state.last_analysis

# Fonction d'affichage des résultats
def display_results(image, label, confidence, db, plant_name, condition):
    """Affiche les résultats de l'analyse"""
    
    # Affichage du diagnostic
    st.markdown("### Diagnostic")
    st.markdown(f"**{label}**")
    
    # Niveau de confiance avec indicateur visuel
    confidence_percent = confidence * 100
    if confidence_percent >= 80:
        confidence_class = "confidence-high"
        confidence_text = "Élevé"
    elif confidence_percent >= 60:
        confidence_class = "confidence-medium"
        confidence_text = "Moyen"
    else:
        confidence_class = "confidence-low"
        confidence_text = "Faible"
    
    st.markdown(f"**Confiance :** <span class='{confidence_class}'>{confidence_percent:.1f}% ({confidence_text})</span>", unsafe_allow_html=True)
    st.progress(confidence)
    
    # Bouton de sauvegarde
    if 'user_info' in st.session_state:
        if st.button("Enregistrer cette analyse", key="save_analysis"):
            success = save_to_firebase(
                db, 
                label, 
                confidence,
                image_size=f"{image.size[0]}x{image.size[1]}",
                plant_name=plant_name,
                condition=condition
            )
            if success:
                st.success("Analyse enregistrée avec succès")
            else:
                st.warning("Impossible d'enregistrer l'analyse (Firebase non configuré)")

def validate_session_token(db, session_token):
    """Valide un token de session et retourne les informations de l'utilisateur."""
    if not session_token:
        return None
        
    try:
        session_ref = db.collection("sessions").document(session_token).get()
        if session_ref.exists:
            session_data = session_ref.to_dict()
            if session_data["expires_at"] > datetime.utcnow():
                return session_data["user_info"]
    except Exception as e:
        st.error(f"Erreur de validation de session: {e}")
        
    return None

def display_user_info():
    """Affiche les informations de l'utilisateur avec sa photo."""
    if 'user_info' in st.session_state:
        user_info = st.session_state.user_info
        
        # Afficher la photo de profil si disponible
        picture_url = user_info.get('picture')
        user_name = user_info.get('name', user_info.get('email', 'Utilisateur'))
        user_email = user_info.get('email', '')
        
        # Créer un conteneur pour le profil utilisateur
        st.sidebar.markdown(
            f"""
            <div class="user-profile">
                <div>
                    {"<img src='" + picture_url + "' class='user-avatar' onerror=\"this.style.display='none'; this.parentElement.innerHTML='👤';\">" if picture_url else "👤"}
                </div>
                <div class="user-info">
                    <div class="user-name">Connecté en tant que :</div>
                    <div class="user-name">{user_name}</div>
                    <div class="user-email">{user_email}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def display_weather_button():
    """Affiche le bouton de météo dans la sidebar."""
    # Ajouter un séparateur si l'utilisateur est connecté
    if 'user_info' in st.session_state:
        st.sidebar.markdown("---")
    
    # Gestion de la localisation et météo
    if 'location_granted' not in st.session_state:
        st.session_state.location_granted = False
    if 'location_requested' not in st.session_state:
        st.session_state.location_requested = False
        
    # Afficher le bouton de localisation uniquement si pas encore activée
    if not st.session_state.location_granted:
        if st.sidebar.button("Activer météo", key="enable_weather"):
            st.session_state.location_requested = True
            st.rerun()
    else:
        st.sidebar.success("Météo activée")
        if 'weather_data' in st.session_state:
            temp = st.session_state.weather_data['temperature']
            humidity = st.session_state.weather_data['humidity']
            st.sidebar.info(f"Température: {temp}°C")
            st.sidebar.info(f"Humidité: {humidity}%")
    
    # Vérifier si la localisation a été demandée
    if st.session_state.location_requested:
        location = streamlit_geolocation()
        if location and location.get('latitude') and location.get('longitude'):
            st.session_state.user_location = {
                "latitude": location['latitude'],
                "longitude": location['longitude']
            }
            st.session_state.location_granted = True
            st.session_state.location_requested = False
            get_weather_data()
            st.rerun()

# Interface principale
def main():
    db = init_firebase()
    
    # Logique de session au démarrage
    session_token = st.query_params.get("session_token")
    if 'user_info' not in st.session_state:
        user_info = validate_session_token(db, session_token)
        if user_info:
            st.session_state.user_info = user_info
            
    handle_auth_callback()

    gemini_available = init_gemini()
    
    # Affichage conditionnel de la connexion/déconnexion
    if 'user_info' in st.session_state:
        # Afficher les informations utilisateur avec photo
        display_user_info()
        
        # Afficher le bouton de météo
        display_weather_button()
        
        # Bouton de déconnexion
        st.sidebar.markdown("---")
        if st.sidebar.button("Se déconnecter"):
            # Invalider la session côté serveur
            if session_token:
                try:
                    db.collection("sessions").document(session_token).delete()
                except Exception as e:
                    st.warning(f"Erreur de déconnexion: {e}")
            
            # Nettoyer les états de session
            keys_to_remove = ['user_info', 'location_granted', 'location_requested', 
                             'user_location', 'weather_data', 'last_analysis']
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Redirect to clear session token from URL
            redirect_uri = os.environ.get("REDIRECT_URI", "")
            st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_uri}">', unsafe_allow_html=True)
            st.stop()
    else:
        with st.sidebar:
            display_login_button()
            # Afficher le bouton de météo même si non connecté
            st.markdown("---")
            display_weather_button()

    # Gestion de l'état de la caméra
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    
    # Header
    st.markdown('<div class="main-title">PhytoSavior</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Système intelligent d\'analyse des maladies des plantes</div>', unsafe_allow_html=True)
    
    # Métriques
    if st.session_state.get('location_granted', False) and 'weather_data' in st.session_state:
        col1, col2, col3, col4, col5 = st.columns(5)
    else:
        col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Maladies détectables", len(CLASSES))
    with col2:
        if db and 'user_info' in st.session_state:
            count = get_total_predictions(db)
        else:
            count = 0
        st.metric("Analyses effectuées", count)
    with col3:
        st.metric("Analyse avancée", "IA")
    if st.session_state.get('location_granted', False) and 'weather_data' in st.session_state:
        with col4:
            st.metric("Température", f"{st.session_state.weather_data['temperature']} °C")
        with col5:
            st.metric("Humidité", f"{st.session_state.weather_data['humidity']} %")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Onglets principaux
    tab1, tab2 = st.tabs(["Importer une image", "Utiliser la caméra"])
    
    with tab1:
        st.subheader("Importer une image")
        st.write("Téléchargez une photo de feuille de plante")

        uploaded_file = st.file_uploader(
            "Sélectionner une image (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="file_uploader",
            on_change=clear_analysis_state  # Nettoyer l'état si une nouvelle image est uploadée
        )

        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.image(img, caption="Aperçu de l'image", width=400)

            if st.button("Analyser cette image", type="primary", key="analyze_upload"):
                if gemini_available:
                    with st.spinner("Validation de l'image..."):
                        if not validate_plant_image(img):
                            st.error("Image non valide: L'image n'est pas une feuille de plante.")
                            st.stop()
                
                with st.spinner("Analyse en cours..."):
                    try:
                        label, confidence = predict(img)
                        st.session_state.last_analysis = {
                            "image": img,
                            "label": label,
                            "confidence": confidence
                        }
                    except Exception as e:
                        st.error(f"Erreur d'analyse: {e}")

        # Afficher les résultats si une analyse a été effectuée
        if 'last_analysis' in st.session_state and st.session_state.last_analysis:
            analysis = st.session_state.last_analysis
            plant_name, condition = extract_plant_info(analysis["label"])
            display_results(analysis["image"], analysis["label"], analysis["confidence"], db, plant_name, condition)

            if gemini_available:
                with st.spinner("Génération de recommandations adaptées aux conditions..."):
                    recommendation = get_plant_recommendation(analysis["label"], analysis["confidence"], plant_name, condition)
                    st.markdown("### Recommandations adaptées")
                    st.markdown(recommendation)
    
    with tab2:
        st.subheader("Utiliser la caméra")
        st.write("Prendre une photo avec votre caméra")
        
        # Contrôle de la caméra
        if not st.session_state.get('camera_active', False):
            if st.button("Activer la caméra", type="primary"):
                st.session_state.camera_active = True
                clear_analysis_state()
                st.rerun()
        else:
            st.info("Caméra activée - prenez une photo claire d'une feuille.")
            
            img_file_buffer = st.camera_input("Prendre une photo", on_change=clear_analysis_state)

            if img_file_buffer is not None:
                img = Image.open(img_file_buffer)
                st.image(img, caption="Photo capturée", width=400)

                if st.button("Analyser cette photo", type="primary"):
                    if gemini_available:
                        with st.spinner("Validation de la photo..."):
                            if not validate_plant_image(img):
                                st.error("Photo non valide: La photo ne semble pas montrer une feuille de plante.")
                                st.stop()

                    with st.spinner("Analyse en cours..."):
                        try:
                            label, confidence = predict(img)
                            st.session_state.last_analysis = {
                                "image": img,
                                "label": label,
                                "confidence": confidence
                            }
                        except Exception as e:
                            st.error(f"Erreur d'analyse: {e}")
            
            if st.button("Désactiver la caméra"):
                st.session_state.camera_active = False
                clear_analysis_state()
                st.rerun()
    
    # Guide d'utilisation
    with st.expander("Guide d'utilisation", expanded=False):
        st.markdown("""
        ### Conseils pour une meilleure analyse
        
        Prise de photo :
        - Utilisez un bon éclairage naturel
        - Placez la feuille au centre de l'image
        - Évitez les ombres portées
        - Assurez-vous que la photo est nette
        
        Sujet à photographier :
        - Feuilles présentant des symptômes visibles
        - Plusieurs feuilles si possible
        - Différents angles pour une analyse complète
        
        Important :
        - Les résultats sont indicatifs
        - Consultez un expert pour confirmation
        - La qualité d'image influence la précision
        - Activez la météo pour des recommandations adaptées aux conditions locales
        """)
    
    # Pied de page
    st.markdown("---")
    st.caption("Solution proposée par Barka Fidèle et Gérard M | 2025 | v1.0")

if __name__ == "__main__":
    main()
