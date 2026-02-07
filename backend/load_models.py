import joblib

def load_model_vehicle():
    model_path = 'model_wts/vehicle_model_weights.pkl'
    features_path = 'model_wts/vehicle_model_features.pkl'

    model = joblib.load(model_path)
    features = joblib.load(features_path)

    return model, features

def load_model_bank():
    model_path = 'model_wts/bank_model_weights.pkl'
    features_path = 'model_wts/bank_model_features.pkl'

    model = joblib.load(model_path)
    features = joblib.load(features_path)

def load_model_ecommerce():
    model_path = 'model_wts/ecommerce_model_weights.pkl'
    features_path = 'model_wts/ecommerce_model_features.pkl'

    model = joblib.load(model_path)
    features = joblib.load(features_path)

    return model, features

def load_model_eth():
    model_path = 'model_wts/ethereum_model_weights.pkl'
    model = joblib.load(model_path)

    return model