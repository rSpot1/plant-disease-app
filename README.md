# PhytoSavior 🌱

Système intelligent d'analyse des maladies des plantes utilisant l'intelligence artificielle pour détecter et diagnostiquer 57 maladies différentes sur diverses cultures.

## 🎯 Fonctionnalités

- Détection automatique : Analyse d'images de feuilles pour identifier les maladies
- IA avancée : cnn
- Recommandations contextuelles : Suggestions de traitement adaptées à la météo locale
- Historique personnel : Suivi de vos analyses avec Firebase
- Authentification Google : Connexion sécurisée et données personnalisées
- Données météo : Intégration avec Open-Meteo pour des conseils adaptés

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Étapes

1. Cloner le dépôt
```bash
git clone https://github.com/rSpot1/plant-disease-app.git
cd plant-disease-app
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Configurer les secrets
Créer un fichier `.streamlit/secrets.toml` avec :
```toml
# Google OAuth
GOOGLE_CLIENT_ID = "votre_client_id"
GOOGLE_CLIENT_SECRET = "votre_client_secret"
REDIRECT_URI = "http://localhost:8501"

# Gemini API
GEMINI_API_KEY = "votre_api_key"

# Firebase (Service Account)
FIREBASE_TYPE = "service_account"
FIREBASE_PROJECT_ID = "votre_project_id"
FIREBASE_PRIVATE_KEY_ID = "votre_key_id"
FIREBASE_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL = "firebase-adminsdk@votre-projet.iam.gserviceaccount.com"
FIREBASE_CLIENT_ID = "votre_client_id"
FIREBASE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
FIREBASE_TOKEN_URI = "https://oauth2.googleapis.com/token"
FIREBASE_AUTH_PROVIDER_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
FIREBASE_CLIENT_CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

4. Ajouter le modèle
Placer votre fichier `model.pth` à la racine du projet

5. Lancer l'application
```bash
streamlit run app.py
```

## 📊 Maladies Détectables

L'application peut détecter 57 maladies sur 14 cultures :
- Pommier : Tavelure, pourriture noire
- Manioc : Bactériose, stries brunes, mosaïque
- Maïs : Rouille, brûlure des feuilles
- Tomate : Mildiou, taches bactériennes, virus
- Pomme de terre : Mildiou précoce/tardif
- Mangue : Anthracnose, oïdium
- Riz : Pyriculariose, tache brune
- Et plus...

## 🛠️ Structure du Projet

```
phytosavior/
├── app.py                 # Application principale
├── inference.py           # Logique de prédiction
├── auth.py               # Authentification Google
├── requirements.txt      # Dépendances
├── model.pth            # Modèle entraîné
└── pages/
    └── 1_Statistiques.py # Page des statistiques
```

## 🔐 Configuration des Services

### Google OAuth
1. Créer un projet sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activer l'API OAuth 2.0
3. Créer des identifiants OAuth avec l'URI de redirection appropriée

### Firebase
1. Créer un projet sur [Firebase Console](https://console.firebase.google.com/)
2. Activer Firestore Database
3. Générer une clé de service account (JSON)
4. Copier les informations dans `secrets.toml`

### Gemini API
1. Obtenir une clé API sur [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Ajouter la clé dans `secrets.toml`

## 📱 Utilisation

1. Se connecter avec votre compte Google
2. Activer la météo pour des recommandations contextuelles
3. Importer une image ou **utiliser la caméra**
4. Analyser l'image pour obtenir le diagnostic
5. Consulter les recommandations de traitement
6. Enregistrer l'analyse dans votre historique

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request



## 👥 Auteurs

- **Barka Fidèle** - Développement initial
- **Gérard Mbaïnabe** - Contribution

## 🙏 Remerciements

- Kaggle pour les données d'entraînement
- Google Gemini pour l'IA générative
- Open-Meteo pour les données météorologiques
- Communauté Streamlit

## 📞 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contacter les auteurs

---

**Version** : 1.0  
**Dernière mise à jour** : 2025
