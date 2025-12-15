import streamlit as st
import pandas as pd
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app import init_firebase, get_history

st.set_page_config(
    page_title="Statistiques - Plant Disease Scanner",
    page_icon="📊",
    layout="wide"
)

db = init_firebase()

if 'user_info' in st.session_state:
    st.markdown("<h1>Mes Statistiques</h1>", unsafe_allow_html=True)

    if db:
        user_history = get_history(db, limit=1000)
        if user_history:
            df = pd.DataFrame(user_history)
            df['date'] = pd.to_datetime(df['date'])

            st.markdown("<h3>Analyses par jour</h3>", unsafe_allow_html=True)
            analyses_par_jour = df.set_index('date').resample('D').size()
            st.line_chart(analyses_par_jour)

            st.markdown("<h3>Confiance des analyses</h3>", unsafe_allow_html=True)
            confiance_df = df[['date', 'confidence']].set_index('date')
            st.line_chart(confiance_df)
        else:
            st.info("Vous n'avez pas encore d'analyses enregistrées.")
    else:
        st.warning("Firebase n'est pas configuré. Les statistiques ne sont pas disponibles.")

    # Section historique
    st.markdown("---")
    st.subheader("Historique récent")
    
    if db:
        history = get_history(db, limit=10)
        if history:
            for item in history:
                date_str = item.get('date', '')
                if 'T' in date_str:
                    try:
                        date_obj = pd.to_datetime(date_str)
                        display_date = date_obj.strftime("%d/%m/%Y %H:%M")
                    except:
                        display_date = date_str
                else:
                    display_date = date_str
                
                disease_label = item.get('disease_label', 'Non spécifié')
                confidence_val = item.get('confidence', 0)
                
                weather_info = ""
                if 'temperature' in item and 'humidity' in item:
                    weather_info = f"<br><small>Météo: {item['temperature']}°C, {item['humidity']}%</small>"

                location_info = ""
                if 'latitude' in item and 'longitude' in item:
                    location_info = f"<br><small>Localisation: {item['latitude']:.4f}, {item['longitude']:.4f}</small>"

                st.markdown(f"""
                <div class="history-item">
                    <strong>{display_date}</strong><br>
                    {disease_label}<br>
                    <small>Confiance : {confidence_val}%</small>
                    {weather_info}
                    {location_info}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucune analyse enregistrée")
    else:
        st.warning("Firebase n'est pas configuré. L'historique n'est pas disponible.")
else:
    st.warning("Veuillez vous connecter pour accéder à vos statistiques.")
    st.stop()