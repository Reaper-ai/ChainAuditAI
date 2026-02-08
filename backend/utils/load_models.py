import joblib
import os

# Get the absolute path to the project root
# internal path: backend/utils/load_models.py -> go up 3 levels to root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, 'model_wts')

def load_features(filename):
    """Safely load features file using absolute path."""
    path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(path):
        return joblib.load(path)
    print(f"WARNING: Feature file not found at {path}")
    return None

def get_model_path(filename):
    """Get absolute path for model weights."""
    return os.path.join(MODEL_DIR, filename)

def load_model_vehicle():
    model = joblib.load(get_model_path('vehicle_model_weights.pkl'))
    features = load_features('vehicle_model_features.pkl')
    return model, features

def load_model_bank():
    model = joblib.load(get_model_path('bank_model_weights.pkl'))
    features = load_features('bank_model_features.pkl')
    return model, features

def load_model_ecommerce():
    model = joblib.load(get_model_path('ecommerce_model_weights.pkl'))
    features = load_features('ecommerce_model_features.pkl')
    return model, features

def load_model_eth():
    model = joblib.load(get_model_path('ethereum_model_weights.pkl'))
    # Ethereum model relies on numeric features only, no feature file needed
    return model, None