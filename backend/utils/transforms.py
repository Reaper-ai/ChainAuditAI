import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def categorize_age(age):
    """
    Categorize age into bins.
    """
    if age <= 20:
        return 0
    elif age <= 40:
        return 1
    elif age <= 65:
        return 2
    else:
        return 3


def transform_vehicle_fraud_data(raw_data, selected_features=None):
    """
    Transform raw vehicle insurance fraud data through all preprocessing steps.
    FIXED: Explicitly handles binary columns for single-row inference.
    """
    
    # Create a copy to avoid modifying original data
    df = raw_data.copy()
    
    # ===== STEP 1: Label Encoding of Binary Columns (FIXED) =====
    # We cannot use df.nunique() == 2 because it fails on single rows.
    # We use explicit mapping assuming alphabetical sorting (standard LabelEncoder behavior).
    binary_mappings = {
        'AccidentArea': {'Rural': 0, 'Urban': 1},
        'Sex': {'Female': 0, 'Male': 1},
        'Fault': {'Policy Holder': 0, 'Third Party': 1},
        'PoliceReportFiled': {'No': 0, 'Yes': 1},
        'WitnessPresent': {'No': 0, 'Yes': 1},
        'AgentType': {'External': 0, 'Internal': 1}
    }

    for col, mapping in binary_mappings.items():
        if col in df.columns:
            # Only map if it's currently a string/object
            if df[col].dtype == 'object':
                # Map and fill unknowns with 0 to be safe
                df[col] = df[col].map(mapping).fillna(0).astype(int)
    
    # ===== STEP 2: Manual Mapping for Specific Columns =====
    vehicleprice_label = {
        'more than 69000': 1, 
        '20000 to 29000': 0,  
        '30000 to 39000': 0, 
        'less than 20000': 1, 
        '40000 to 59000': 1, 
        '60000 to 69000': 0
    }
    
    ageofvehicle_label = {
        'new': 2, 
        '2 years': 0, 
        '3 years': 2, 
        '4 years': 2, 
        '5 years': 1, 
        '6 years': 1, 
        '7 years': 0, 
        'more than 7': 0
    }
    
    basepolicy_label = {
        'Liability': 0, 
        'Collision': 1, 
        'All Perils': 2
    }
    
    if 'VehiclePrice' in df.columns:
        df['VehiclePrice'] = df['VehiclePrice'].map(vehicleprice_label).fillna(0).astype(int)
    
    if 'AgeOfVehicle' in df.columns:
        df['AgeOfVehicle'] = df['AgeOfVehicle'].map(ageofvehicle_label).fillna(0).astype(int)
    
    if 'BasePolicy' in df.columns:
        df['BasePolicy'] = df['BasePolicy'].map(basepolicy_label).fillna(0).astype(int)
    
    # ===== STEP 3: Drop Useless Columns =====
    useless_columns = ['Month', 'WeekOfMonth', 'DayOfWeek', 'DayOfWeekClaimed', 
                       'WeekOfMonthClaimed', 'PolicyNumber']
    
    columns_to_drop = [col for col in useless_columns if col in df.columns]
    df = df.drop(columns=columns_to_drop, axis=1)
    
    # ===== STEP 4: Convert Data Types to String for One-Hot Encoding =====
    dtype_change_string = ['RepNumber', 'Deductible', 'Year']
    
    for col in dtype_change_string:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    # ===== STEP 5: One-Hot Encoding =====
    onehot_encoding_columns = [
        'Make', 'MonthClaimed', 'MaritalStatus', 'PolicyType', 'VehicleCategory', 
        'RepNumber', 'Deductible', 'Days_Policy_Accident', 'Days_Policy_Claim', 
        'PastNumberOfClaims', 'AgeOfPolicyHolder', 'NumberOfSuppliments', 
        'AddressChange_Claim', 'NumberOfCars', 'Year'
    ]
    
    # Only encode columns that exist in the dataframe
    columns_to_encode = [col for col in onehot_encoding_columns if col in df.columns]
    
    if columns_to_encode:
        df = pd.get_dummies(df, columns=columns_to_encode)
    
    # ===== STEP 6: Drop Constant Features =====
    # (Skipping this step for inference safety - we might only have 1 row)
    # If we drop columns here based on "sum <= 5", we might drop active features in single-row mode.
    # Instead, we rely on 'selected_features' at the end to filter correctly.
    
    # ===== STEP 7: Age Outlier Handling and Imputation =====
    if 'Age' in df.columns:
        # Replace 0s and outliers (> 74) with NaN
        df['Age'] = df['Age'].apply(lambda x: np.nan if x == 0 or x > 74 else x)
        
        # Simple median imputation for missing age values
        if df['Age'].isnull().any():
            age_median = 40 # Default fallback
            df['Age'] = df['Age'].fillna(age_median)
        
        # Round up floats
        df['Age'] = df['Age'].apply(lambda x: round(x))
        
        # Categorize Age
        df['Age'] = df['Age'].apply(categorize_age)
    
    # ===== STEP 8: Feature Selection =====
    # If selected_features are provided (for inference), select only those columns
    if selected_features is not None:
        # Ensure all required features exist, add missing ones as 0
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        
        # Select only the required features in the correct order
        df = df[selected_features]
    
    return df


def encode_cyclical(df, col, max_val):
    """
    Create sin and cos features for cyclical variables.
    """
    df[col + '_sin'] = np.sin(2 * np.pi * df[col] / max_val)
    df[col + '_cos'] = np.cos(2 * np.pi * df[col] / max_val)
    return df


def transform_ethereum_fraud_data(raw_data, selected_features=None):
    """
    Transform raw Ethereum transaction fraud data.
    """
    df = raw_data.copy()
    epsilon = 1e-6
    
    # Ratio & Velocity Features
    if 'total_tx_sent_malicious' in df.columns:
        df['ratio_malicious_sent'] = df['total_tx_sent_malicious'] / (df['total_tx_sent'] + epsilon)
    if 'total_tx_sent_unique' in df.columns:
        df['ratio_unique_sent'] = df['total_tx_sent_unique'] / (df['total_tx_sent'] + epsilon)
    if 'total_received' in df.columns:
        df['velocity_value_received'] = df['total_received'] / (df['time_diff_first_last_received'] + epsilon)
    
    # Statistical Features
    if 'variance_value_received' in df.columns:
        df['received_coef_variation'] = np.sqrt(df['variance_value_received']) / (df['mean_value_received'] + epsilon)
    
    df = df.replace([np.inf, -np.inf], 0)
    
    # Cyclical Encoding
    if 'Hour' in df.columns:
        df = encode_cyclical(df, 'Hour', 24)
    if 'Day' in df.columns:
        df = encode_cyclical(df, 'Day', 31)
    
    # Drop Columns
    drop_cols = [
        'confirmations', 'variance_value_received', 'total_tx_sent_malicious',
        'total_tx_sent_unique', 'blockNumber', 'Month', 'Hour', 'Day', 'Fraud',
        'ratio_malicious_sent'
    ]
    columns_to_drop = [col for col in drop_cols if col in df.columns]
    df = df.drop(columns=columns_to_drop, axis=1)
    
    # Feature Selection
    if selected_features is not None:
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        df = df[selected_features]
    
    return df


def transform_ecommerce_fraud_data(raw_data, selected_features=None):
    """
    Transform raw e-commerce transaction fraud data.
    """
    df = raw_data.copy()
    
    # Clean Age
    if 'Customer Age' in df.columns:
        mean_age = 30 # Default
        df.loc[df['Customer Age'] < 10, 'Customer Age'] = mean_age
    
    # Address Match
    if 'Shipping Address' in df.columns and 'Billing Address' in df.columns:
        df['Address Match'] = (df['Shipping Address'] == df['Billing Address']).astype(int)
    
    # Drop Cols
    drop_cols = ['Transaction ID', 'Customer Location', 'Shipping Address', 'Billing Address']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], axis=1)
    
    # One-Hot Encoding
    categorical_cols = ['Payment Method', 'Product Category', 'Device Used']
    columns_to_encode = [col for col in categorical_cols if col in df.columns]
    if columns_to_encode:
        df = pd.get_dummies(df, columns=columns_to_encode, drop_first=False)
    
    # Standard Scaling
    numeric_features = ['Transaction Amount', 'Quantity', 'Customer Age', 'Account Age Days', 'Transaction Hour']
    features_to_scale = [col for col in numeric_features if col in df.columns]
    if features_to_scale:
        scaler = StandardScaler()
        df[features_to_scale] = scaler.fit_transform(df[features_to_scale])
    
    # Time/Agg Features
    if 'Customer ID' in df.columns and 'Transaction Amount' in df.columns:
        df['Customer_Avg_Amount'] = df['Transaction Amount'] # Simplified for single row
    
    # Risk Features
    if 'Transaction Amount' in df.columns:
        df['Amount_vs_Avg'] = 1.0
        if 'Account Age Days' in df.columns:
            df['Risk_New_High_Spend'] = df['Transaction Amount'] / (df['Account Age Days'] + 1)
        if 'Quantity' in df.columns:
            df['Amount_per_Item'] = df['Transaction Amount'] / (df['Quantity'] + 1e-6)
        if 'Address Match' in df.columns:
            df['Risk_Mismatch'] = df['Transaction Amount'] * (1 - df['Address Match'])
    
    # Cyclical Time
    if 'Transaction Date' in df.columns:
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        df['Month'] = df['Transaction Date'].dt.month
        df['Day'] = df['Transaction Date'].dt.day
        df['Hour'] = df['Transaction Date'].dt.hour
        df['DayOfWeek'] = df['Transaction Date'].dt.dayofweek
        
        df = encode_cyclical(df, 'Month', 12)
        df = encode_cyclical(df, 'Day', 31)
        df = encode_cyclical(df, 'Hour', 24)
        df = encode_cyclical(df, 'DayOfWeek', 7)
        
        df = df.drop(columns=['Month', 'Day', 'Hour', 'DayOfWeek'])
    
    # Drop Remaining
    final_drop_cols = ['Transaction Date', 'Transaction Hour', 'IP Address', 'Customer ID', 'Account Age Days']
    df = df.drop(columns=[c for c in final_drop_cols if c in df.columns], axis=1)
    
    # Feature Selection
    if selected_features is not None:
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        df = df[selected_features]
    
    return df


def transform_bank_fraud_data(raw_data, selected_features=None):
    """
    Transform raw bank account fraud data.
    """
    df = raw_data.copy()
    
    # Fill missing with safe defaults
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Categorical handling
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].astype('category').cat.codes

    # Feature Selection
    if selected_features is not None:
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        df = df[selected_features]
        
    return df