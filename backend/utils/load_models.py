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
    """Load vehicle model and extract feature names from the model itself."""
    model = joblib.load(get_model_path('vehicle_model_weights.pkl'))
    # Extract features from model instead of corrupted feature files
    features = model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else None
    if features:
        print(f"✓ Vehicle model loaded with {len(features)} features")
    return model, features

def load_model_bank():
    """Load bank model and extract feature names from the model itself."""
    model = joblib.load(get_model_path('bank_model_weights.pkl'))
    # Extract features from model instead of corrupted feature files
    features = model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else None
    if features:
        print(f"✓ Bank model loaded with {len(features)} features")
    return model, features

def load_model_ecommerce():
    """Load ecommerce model and extract feature names from the model itself."""
    model = joblib.load(get_model_path('ecommerce_model_weights.pkl'))
    # Extract features from model instead of corrupted feature files
    features = model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else None
    if features:
        print(f"✓ Ecommerce model loaded with {len(features)} features")
    return model, features

def load_model_eth():
    """Load ethereum model and extract feature names from the model itself."""
    model = joblib.load(get_model_path('ethereum_model_weights.pkl'))
    # Extract features from model instead of corrupted feature files
    features = model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else None
    if features:
        print(f"✓ Ethereum model loaded with {len(features)} features")
    return model, features