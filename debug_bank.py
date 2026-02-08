"""Debug script to test bank fraud detection"""
import pandas as pd
import sys
sys.path.insert(0, '/home/gaurav/python/meraki/backend')

from utils.load_models import load_model_bank
from utils.transforms import transform_bank_fraud_data

# Load model
print("Loading bank model...")
model, expected_features = load_model_bank()
print(f"Model loaded: {type(model)}")
print(f"Expected features: {len(expected_features) if expected_features else 'None'}")
if expected_features:
    print(f"First 10 features: {expected_features[:10]}")

# Load test data
print("\nLoading test data...")
df = pd.read_csv('/home/gaurav/python/meraki/data/test_data/bank_test_data.csv')
print(f"Test data shape: {df.shape}")
print(f"Columns: {list(df.columns)[:10]}")

# Get fraud column
fraud_col = 'fraud_bool'
fraud_samples = df[df[fraud_col] == 1]
print(f"\nFraud samples: {len(fraud_samples)}")

# Get one sample
sample = fraud_samples.iloc[0].to_dict()
print(f"\nSample keys: {list(sample.keys())[:15]}")

# Remove fraud label
sample.pop(fraud_col, None)

# Transform
print("\nTransforming data...")
sample_df = pd.DataFrame([sample])
transformed = transform_bank_fraud_data(sample_df, selected_features=None)
print(f"Transformed shape: {transformed.shape}")
print(f"Transformed columns: {list(transformed.columns)[:15]}")

# Check feature alignment
if expected_features:
    print(f"\nModel expects {len(expected_features)} features")
    print(f"Transform created {len(transformed.columns)} features")
    
    # Find missing
    missing_in_transform = set(expected_features) - set(transformed.columns)
    if missing_in_transform:
        print(f"\nMISSING in transform: {list(missing_in_transform)[:10]}")
    
    # Find extra
    extra_in_transform = set(transformed.columns) - set(expected_features)
    if extra_in_transform:
        print(f"\nEXTRA in transform: {list(extra_in_transform)[:10]}")
    
    # Reorder
    print("\nReordering features...")
    for feature in expected_features:
        if feature not in transformed.columns:
            transformed[feature] = 0
    
    transformed = transformed[expected_features]
    print(f"Final shape: {transformed.shape}")
    
    # Predict
    print("\nPredicting...")
    try:
        prediction = model.predict(transformed)
        print(f"Prediction: {prediction[0]}")
        print(f"Fraud score: {int(prediction[0]) * 100}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
