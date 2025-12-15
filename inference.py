import torch
import torch.nn.functional as F
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
from torchvision import models
import torch.nn as nn

# Liste des classes originales
CLASSES = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___healthy',
    'Cassava___bacterial_blight', 'Cassava___brown_streak_disease',
    'Cassava___green_mottle', 'Cassava___healthy', 'Cassava___mosaic_disease',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
    'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight',
    'Corn_(maize)___healthy', 'Orange___Haunglongbing_(Citrus_greening)',
    'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
    'Potato___Early_blight', 'Potato___Late_blight', 'Soybean___healthy',
    'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch',
    'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight',
    'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___healthy',
    'cucumber_Downy_mildew', 'cucumber_Healthy_leaves', 'cucumber_Powdery_mildew',
    'guava_anthracnose', 'guava_healthy', 'guava_insect_bite', 'guava_mix',
    'guava_multiple', 'guava_scorch', 'guava_yld', 'mango_Anthracnose',
    'mango_Bacterial Canker', 'mango_Cutting Weevil', 'mango_Die Back',
    'mango_Gall Midge', 'mango_Healthy', 'mango_Powdery Mildew', 'mango_Sooty Mould',
    'rice_Bacterial Leaf Blight', 'rice_Brown Spot', 'rice_Healthy Rice Leaf',
    'rice_Leaf Blast', 'rice_Leaf scald', 'rice_Sheath Blight',
    'sugarcane_Healthy', 'sugarcane_RedRot', 'sugarcane_Rust', 'sugarcane_Yellow'
]

# Traduction des noms de classes en français
CLASS_NAMES_TRANSLATION = {
    # Pommier
    'Apple___Apple_scab': 'Tavelure du pommier',
    'Apple___Black_rot': 'Pourriture noire du pommier',
    'Apple___healthy': 'Pommier sain',
    
    # Manioc
    'Cassava___bacterial_blight': 'Bactériose du manioc',
    'Cassava___brown_streak_disease': 'Maladie des stries brunes du manioc',
    'Cassava___green_mottle': 'Mosaïque verte du manioc',
    'Cassava___healthy': 'Manioc sain',
    'Cassava___mosaic_disease': 'Maladie mosaïque du manioc',
    
    # Maïs
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': 'Tache grise des feuilles de maïs',
    'Corn_(maize)___Common_rust_': 'Rouille commune du maïs',
    'Corn_(maize)___Northern_Leaf_Blight': 'Brûlure nordique des feuilles de maïs',
    'Corn_(maize)___healthy': 'Maïs sain',
    
    # Orange
    'Orange___Haunglongbing_(Citrus_greening)': 'Greening des agrumes',
    
    # Poivron
    'Pepper,_bell___Bacterial_spot': 'Tache bactérienne du poivron',
    'Pepper,_bell___healthy': 'Poivron sain',
    
    # Pomme de terre
    'Potato___Early_blight': 'Mildiou précoce de la pomme de terre',
    'Potato___Late_blight': 'Mildiou tardif de la pomme de terre',
    'Potato___healthy': 'Pomme de terre saine',
    
    # Soja
    'Soybean___healthy': 'Soja sain',
    
    # Courge
    'Squash___Powdery_mildew': 'Oïdium de la courge',
    
    # Fraise
    'Strawberry___Leaf_scorch': 'Brûlure des feuilles de fraisier',
    
    # Tomate
    'Tomato___Bacterial_spot': 'Tache bactérienne de la tomate',
    'Tomato___Early_blight': 'Mildiou précoce de la tomate',
    'Tomato___Late_blight': 'Mildiou tardif de la tomate',
    'Tomato___Leaf_Mold': 'Moisissure des feuilles de tomate',
    'Tomato___Septoria_leaf_spot': 'Septoriose de la tomate',
    'Tomato___Spider_mites Two-spotted_spider_mite': 'Acariens sur tomate',
    'Tomato___Target_Spot': 'Tache cible de la tomate',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': "Virus de l'enroulement jaune des feuilles de tomate",
    'Tomato___healthy': 'Tomate saine',
    
    # Concombre
    'cucumber_Downy_mildew': 'Mildiou du concombre',
    'cucumber_Healthy_leaves': 'Feuilles de concombre saines',
    'cucumber_Powdery_mildew': 'Oïdium du concombre',
    
    # Goyave
    'guava_anthracnose': 'Anthracnose de la goyave',
    'guava_healthy': 'Goyave saine',
    'guava_insect_bite': 'Piqûres d\'insectes sur goyave',
    'guava_mix': 'Problèmes multiples sur goyave',
    'guava_multiple': 'Infections multiples de la goyave',
    'guava_scorch': 'Brûlure de la goyave',
    'guava_yld': 'Goyave avec symptômes non spécifiques',
    
    # Mangue
    'mango_Anthracnose': 'Anthracnose de la mangue',
    'mango_Bacterial Canker': 'Chancre bactérien de la mangue',
    'mango_Cutting Weevil': 'Charançon de la mangue',
    'mango_Die Back': 'Dépérissement de la mangue',
    'mango_Gall Midge': 'Cécidomyie de la mangue',
    'mango_Healthy': 'Mangue saine',
    'mango_Powdery Mildew': 'Oïdium de la mangue',
    'mango_Sooty Mould': 'Fumagine de la mangue',
    
    # Riz
    'rice_Bacterial Leaf Blight': 'Brûlure bactérienne des feuilles de riz',
    'rice_Brown Spot': 'Tache brune du riz',
    'rice_Healthy Rice Leaf': 'Feuille de riz saine',
    'rice_Leaf Blast': 'Pyriculariose du riz',
    'rice_Leaf scald': 'Échaudure des feuilles de riz',
    'rice_Sheath Blight': 'Pourriture de la gaine du riz',
    
    # Canne à sucre
    'sugarcane_Healthy': 'Canne à sucre saine',
    'sugarcane_RedRot': 'Pourriture rouge de la canne à sucre',
    'sugarcane_Rust': 'Rouille de la canne à sucre',
    'sugarcane_Yellow': 'Jaunissement de la canne à sucre'
}

# Fonction pour convertir le label en texte lisible
def get_readable_label(label):
    """Convertit un label technique en texte compréhensible"""
    return CLASS_NAMES_TRANSLATION.get(label, label)

mean = torch.tensor([0.4973, 0.5281, 0.4352])
std = torch.tensor([0.2211, 0.2039, 0.2514])

transform = transforms.Compose([
    transforms.Lambda(lambda img: img.convert("RGB")),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=mean, std=std)
])

device = "cpu"

def build_model(num_classes: int = 57):
    """Construit le modèle ResNet18"""
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

def load_model(model_path: str, num_classes: int = 57):
    """Charge le modèle entraîné"""
    model = build_model(num_classes)
    # Charger un checkpoint complet ou juste les poids
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    elif isinstance(checkpoint, dict):
        model.load_state_dict(checkpoint)
    else:
        model = checkpoint  # fichier .pkl complet
    model.eval()
    return model

# Charger le modèle globalement
model = load_model("model.pth", num_classes=len(CLASSES))

def predict(image: Image.Image):
    """Effectue une prédiction sur une image"""
    img = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(img)
        probs = F.softmax(output, dim=1)[0].cpu().numpy()
    idx = int(np.argmax(probs))
    original_label = CLASSES[idx]
    readable_label = get_readable_label(original_label)
    return readable_label, float(probs[idx])

# Pour les imports
__all__ = ['predict', 'CLASS_NAMES_TRANSLATION', 'get_readable_label', 'CLASSES']