import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Helper to bin age without crashing
def categorize_age(age):
    if age <= 20: return 0
    elif age <= 40: return 1
    elif age <= 65: return 2
    else: return 3

# Helper for time features
def encode_cyclical(df, col, max_val):
    df[col + '_sin'] = np.sin(2 * np.pi * df[col] / max_val)
    df[col + '_cos'] = np.cos(2 * np.pi * df[col] / max_val)
    return df

# ==========================================
# 1. VEHICLE TRANSFORM (No Scaling)
# ==========================================
def transform_vehicle_fraud_data(raw_data, selected_features=None):
    df = raw_data.copy()
    
    # 1. Binary Mappings (Manual to be safe)
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
            # Map strings to 0/1, default to 0 if unknown
            df[col] = df[col].map(mapping).fillna(0).astype(int)

    # 2. Ordered Categorical Mappings
    if 'VehiclePrice' in df.columns:
        df['VehiclePrice'] = df['VehiclePrice'].map({
            'more than 69000': 1, '20000 to 29000': 0, '30000 to 39000': 0, 
            'less than 20000': 1, '40000 to 59000': 1, '60000 to 69000': 0
        }).fillna(0)
    
    if 'AgeOfVehicle' in df.columns:
        df['AgeOfVehicle'] = df['AgeOfVehicle'].map({
            'new': 2, '2 years': 0, '3 years': 2, '4 years': 2, 
            '5 years': 1, '6 years': 1, '7 years': 0, 'more than 7': 0
        }).fillna(0)

    if 'BasePolicy' in df.columns:
        df['BasePolicy'] = df['BasePolicy'].map({'Liability': 0, 'Collision': 1, 'All Perils': 2}).fillna(0)

    # 3. Drop Useless Columns
    drop_cols = ['Month', 'WeekOfMonth', 'DayOfWeek', 'DayOfWeekClaimed', 'WeekOfMonthClaimed', 'PolicyNumber']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], axis=1)

    # 4. One-Hot Encoding (drop_first=False to keep all columns)
    onehot_cols = ['Make', 'MonthClaimed', 'MaritalStatus', 'PolicyType', 'VehicleCategory', 'RepNumber', 'Deductible', 'Days_Policy_Accident', 'Days_Policy_Claim', 'PastNumberOfClaims', 'AgeOfPolicyHolder', 'NumberOfSuppliments', 'AddressChange_Claim', 'NumberOfCars', 'Year']
    existing_cols = [c for c in onehot_cols if c in df.columns]
    if existing_cols:
        df = pd.get_dummies(df, columns=existing_cols, drop_first=False)

    # 5. Age Cleanup
    if 'Age' in df.columns:
        df['Age'] = df['Age'].apply(lambda x: 40 if x == 0 or x > 74 else x)
        df['Age'] = df['Age'].apply(categorize_age)

    # 6. Feature Selection (Match Model Expectations)
    if selected_features is not None:
        missing = list(set(selected_features) - set(df.columns))
        if missing:
            df[missing] = 0
        df = df[selected_features]
        
    return df

# ==========================================
# 2. E-COMMERCE TRANSFORM (No Scaling)
# ==========================================
def transform_ecommerce_fraud_data(raw_data, selected_features=None):
    df = raw_data.copy()
    
    # 1. Basic Cleanup
    if 'Customer Age' in df.columns:
        df.loc[df['Customer Age'] < 10, 'Customer Age'] = 30
    
    if 'Shipping Address' in df.columns and 'Billing Address' in df.columns:
        df['Address Match'] = (df['Shipping Address'] == df['Billing Address']).astype(int)
    
    # 2. Drop IDs and Text
    drop_cols = ['Transaction ID', 'Customer Location', 'Shipping Address', 'Billing Address']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], axis=1)
    
    # 3. One-Hot Encoding
    cat_cols = ['Payment Method', 'Product Category', 'Device Used']
    cols_to_encode = [c for c in cat_cols if c in df.columns]
    if cols_to_encode:
        df = pd.get_dummies(df, columns=cols_to_encode, drop_first=False)
    
    # 4. Feature Engineering (No Scaling)
    if 'Customer ID' in df.columns and 'Transaction Amount' in df.columns:
        df['Customer_Avg_Amount'] = df['Transaction Amount'] # Simplified for single row
    
    if 'Transaction Amount' in df.columns:
        df['Amount_vs_Avg'] = 1.0
        if 'Account Age Days' in df.columns: 
            df['Risk_New_High_Spend'] = df['Transaction Amount'] / (df['Account Age Days'] + 1)
        if 'Quantity' in df.columns: 
            df['Amount_per_Item'] = df['Transaction Amount'] / (df['Quantity'] + 1e-6)
        if 'Address Match' in df.columns: 
            df['Risk_Mismatch'] = df['Transaction Amount'] * (1 - df['Address Match'])
    
    # 5. Time Encoding
    if 'Transaction Date' in df.columns:
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        for unit, max_val in [('Month', 12), ('Day', 31), ('Hour', 24), ('DayOfWeek', 7)]:
            val = getattr(df['Transaction Date'].dt, unit.lower())
            df = encode_cyclical(df, unit, max_val)
    
    # 6. Final Drops
    final_drop = ['Transaction Date', 'Transaction Hour', 'IP Address', 'Customer ID', 'Account Age Days']
    df = df.drop(columns=[c for c in final_drop if c in df.columns], axis=1)
    
    # 7. Alignment
    if selected_features is not None:
        missing = list(set(selected_features) - set(df.columns))
        if missing:
            df[missing] = 0
        df = df[selected_features]
    
    return df

# ==========================================
# 3. BANK TRANSFORM (No Scaling)
# ==========================================
def transform_bank_fraud_data(raw_data, selected_features=None):
    df = raw_data.copy()
    df = df.fillna(0)
    
    # Encode Categoricals
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].astype('category').cat.codes

    # Alignment
    if selected_features is not None:
        missing = list(set(selected_features) - set(df.columns))
        if missing:
            df[missing] = 0
        df = df[selected_features]
        
    return df

# ==========================================
# 4. ETHEREUM TRANSFORM (No Scaling)
# ==========================================
def transform_ethereum_fraud_data(raw_data, selected_features=None):
    df = raw_data.copy()
    epsilon = 1e-6
    
    # Ratios
    if 'total_tx_sent_malicious' in df.columns:
        df['ratio_malicious_sent'] = df['total_tx_sent_malicious'] / (df['total_tx_sent'] + epsilon)
    if 'total_tx_sent_unique' in df.columns:
        df['ratio_unique_sent'] = df['total_tx_sent_unique'] / (df['total_tx_sent'] + epsilon)
    if 'total_received' in df.columns:
        df['velocity_value_received'] = df['total_received'] / (df['time_diff_first_last_received'] + epsilon)
    
    # Time
    if 'Hour' in df.columns: df = encode_cyclical(df, 'Hour', 24)
    if 'Day' in df.columns: df = encode_cyclical(df, 'Day', 31)
    
    # Drop
    drop_cols = ['confirmations', 'variance_value_received', 'total_tx_sent_malicious', 
                 'total_tx_sent_unique', 'blockNumber', 'Month', 'Hour', 'Day', 'Fraud', 'ratio_malicious_sent']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], axis=1)
    
    # Alignment
    if selected_features is not None:
        missing = list(set(selected_features) - set(df.columns))
        if missing:
            df[missing] = 0
        df = df[selected_features]
    
    return df