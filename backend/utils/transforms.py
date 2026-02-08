import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def categorize_age(age):
    """
    Categorize age into bins.
    
    Args:
        age: Age value
    
    Returns:
        Category (0-3)
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
    
    This function applies all the feature engineering and transformations done 
    in the vechicle-fraudmain.ipynb notebook, including:
    1. Label encoding of binary columns
    2. Manual mapping of categorical features
    3. Dropping useless columns
    4. One-hot encoding
    5. Dropping constant features
    6. Age outlier handling and imputation
    7. Age categorization
    8. Feature selection (if selected_features provided)
    
    Args:
        raw_data: pandas DataFrame with raw vehicle insurance data
        selected_features: list of feature names to select (optional, for inference)
    
    Returns:
        Transformed pandas DataFrame ready for model prediction
    """
    
    # Create a copy to avoid modifying original data
    df = raw_data.copy()
    
    # ===== STEP 1: Label Encoding of Binary Columns =====
    binary_columns = [col for col in df.columns if df[col].nunique() == 2 and col != 'FraudFound_P']
    
    le = LabelEncoder()
    for col in binary_columns:
        df[col] = le.fit_transform(df[col].astype(str))
    
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
        df['VehiclePrice'] = df['VehiclePrice'].map(vehicleprice_label)
    
    if 'AgeOfVehicle' in df.columns:
        df['AgeOfVehicle'] = df['AgeOfVehicle'].map(ageofvehicle_label)
    
    if 'BasePolicy' in df.columns:
        df['BasePolicy'] = df['BasePolicy'].map(basepolicy_label)
    
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
    
    df = pd.get_dummies(df, columns=columns_to_encode)
    
    # ===== STEP 6: Drop Constant Features =====
    # Get one-hot encoded columns (those with '_' but not FraudFound_P)
    onehot_encoded_columns = [col for col in df.columns if '_' in col and col != 'FraudFound_P']
    
    constant_features = []
    for col in onehot_encoded_columns:
        if df[col].sum() <= 5:
            constant_features.append(col)
    
    df = df.drop(columns=constant_features, axis=1)
    
    # ===== STEP 7: Age Outlier Handling and Imputation =====
    if 'Age' in df.columns:
        # Replace 0s and outliers (> 74) with NaN
        df['Age'] = df['Age'].apply(lambda x: np.nan if x == 0 or x > 74 else x)
        
        # Simple median imputation for missing age values
        if df['Age'].isnull().any():
            age_median = df['Age'].median()
            if pd.isna(age_median):  # If all ages are null, use default value
                age_median = 40
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
    
    Args:
        df: DataFrame
        col: Column name to encode
        max_val: Maximum value in the cycle (e.g., 24 for hours, 31 for days)
    
    Returns:
        DataFrame with new sin/cos columns
    """
    df[col + '_sin'] = np.sin(2 * np.pi * df[col] / max_val)
    df[col + '_cos'] = np.cos(2 * np.pi * df[col] / max_val)
    return df


def transform_ethereum_fraud_data(raw_data, selected_features=None):
    """
    Transform raw Ethereum transaction fraud data through all preprocessing steps.
    
    This function applies all the feature engineering and transformations done 
    in the eth-fraud-nb.ipynb notebook, including:
    1. Ratio features (malicious/unique transaction ratios)
    2. Velocity features (value received per time)
    3. Statistical features (coefficient of variation)
    4. Cyclical encoding for temporal features
    5. Feature selection
    
    Args:
        raw_data: pandas DataFrame with raw Ethereum transaction data
        selected_features: list of feature names to select (optional, for inference)
    
    Returns:
        Transformed pandas DataFrame ready for model prediction
    """
    
    df = raw_data.copy()
    epsilon = 1e-6
    
    # ===== STEP 1: RATIO FEATURES =====
    df['ratio_malicious_sent'] = df['total_tx_sent_malicious'] / (df['total_tx_sent'] + epsilon)
    df['ratio_unique_sent'] = df['total_tx_sent_unique'] / (df['total_tx_sent'] + epsilon)
    
    # ===== STEP 2: VELOCITY FEATURES =====
    df['velocity_value_received'] = df['total_received'] / (df['time_diff_first_last_received'] + epsilon)
    
    # ===== STEP 3: STATISTICAL FEATURES =====
    df['received_coef_variation'] = np.sqrt(df['variance_value_received']) / (df['mean_value_received'] + epsilon)
    
    # ===== STEP 4: REPLACE INFINITY VALUES =====
    df = df.replace([np.inf, -np.inf], 0)
    
    # ===== STEP 5: SORT BY TIME (if needed for temporal consistency) =====
    if 'Month' in df.columns:
        df = df.sort_values(by='Month').reset_index(drop=True)
    
    # ===== STEP 6: CYCLICAL ENCODING =====
    if 'Hour' in df.columns:
        df = encode_cyclical(df, 'Hour', 24)
    if 'Day' in df.columns:
        df = encode_cyclical(df, 'Day', 31)
    
    # ===== STEP 7: DROP COLUMNS =====
    drop_cols = [
        'confirmations', 
        'variance_value_received', 
        'total_tx_sent_malicious',
        'total_tx_sent_unique',
        'blockNumber',
        'Month',
        'Hour',
        'Day',
        'Fraud',
        'ratio_malicious_sent'
    ]
    
    columns_to_drop = [col for col in drop_cols if col in df.columns]
    df = df.drop(columns=columns_to_drop, axis=1)
    
    # ===== STEP 8: FEATURE SELECTION =====
    if selected_features is not None:
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        df = df[selected_features]
    
    return df

def transform_ecommerce_fraud_data(raw_data, selected_features=None):
    """
    Transform raw e-commerce transaction fraud data.
    FIX: Removed drop_first=True to prevent data loss on single-row inference.
    """
    
    df = raw_data.copy()
    
    # ===== STEP 1: CLEAN CUSTOMER AGE =====
    if 'Customer Age' in df.columns:
        mean_age = df['Customer Age'].mean()
        if pd.isna(mean_age): mean_age = 30 # Default fallback
        df.loc[df['Customer Age'] < 10, 'Customer Age'] = mean_age
    
    # ===== STEP 2: ADDRESS MATCH FEATURE =====
    if 'Shipping Address' in df.columns and 'Billing Address' in df.columns:
        df['Address Match'] = (df['Shipping Address'] == df['Billing Address']).astype(int)
    
    # ===== STEP 3: DROP UNNECESSARY COLUMNS =====
    drop_cols = ['Transaction ID', 'Customer Location', 'Shipping Address', 'Billing Address']
    columns_to_drop = [col for col in drop_cols if col in df.columns]
    df = df.drop(columns=columns_to_drop, axis=1)
    
    # ===== STEP 4: ONE-HOT ENCODING (FIXED) =====
    categorical_cols = ['Payment Method', 'Product Category', 'Device Used']
    columns_to_encode = [col for col in categorical_cols if col in df.columns]
    if columns_to_encode:
        # CRITICAL FIX: drop_first=False so we don't lose the category in single-row inference
        df = pd.get_dummies(df, columns=columns_to_encode, drop_first=False)
    
    # ===== STEP 5: STANDARD SCALING (NUMERIC FEATURES) =====
    numeric_features = ['Transaction Amount', 'Quantity', 'Customer Age', 'Account Age Days', 'Transaction Hour']
    features_to_scale = [col for col in numeric_features if col in df.columns]
    if features_to_scale:
        scaler = StandardScaler()
        df[features_to_scale] = scaler.fit_transform(df[features_to_scale])
    
    # ===== STEP 6: TIME-BASED FEATURES =====
    if 'Customer ID' in df.columns and 'Transaction Amount' in df.columns:
        df['Customer_Avg_Amount'] = df.groupby('Customer ID')['Transaction Amount'].transform('mean')
    
    if 'IP Address' in df.columns:
        if 'Customer ID' in df.columns:
            df['IPs_per_Customer'] = df.groupby('Customer ID')['IP Address'].transform('nunique')
            df['Customers_per_IP'] = df.groupby('IP Address')['Customer ID'].transform('nunique')
            df['Is_Shared_IP'] = (df['Customers_per_IP'] > 5).astype(int)
    
    # ===== STEP 7: RISK FEATURES =====
    if 'Transaction Amount' in df.columns:
        if 'Customer_Avg_Amount' in df.columns:
            df['Amount_vs_Avg'] = df['Transaction Amount'] / (df['Customer_Avg_Amount'] + 1e-6)
        
        if 'Account Age Days' in df.columns:
            df['Risk_New_High_Spend'] = df['Transaction Amount'] / (df['Account Age Days'] + 1)
        
        if 'Quantity' in df.columns:
            df['Amount_per_Item'] = df['Transaction Amount'] / (df['Quantity'] + 1e-6)
        
        if 'Address Match' in df.columns:
            df['Risk_Mismatch'] = df['Transaction Amount'] * (1 - df['Address Match'])
    
    # ===== STEP 8: CYCLICAL TIME ENCODING =====
    if 'Transaction Date' in df.columns:
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
        df['Month'] = df['Transaction Date'].dt.month
        df['Day'] = df['Transaction Date'].dt.day
        df['Hour'] = df['Transaction Date'].dt.hour
        df['DayOfWeek'] = df['Transaction Date'].dt.dayofweek
        
        # Encode cyclically
        df = encode_cyclical(df, 'Month', 12)
        df = encode_cyclical(df, 'Day', 31)
        df = encode_cyclical(df, 'Hour', 24)
        df = encode_cyclical(df, 'DayOfWeek', 7)
        
        # Drop raw temporal features
        df = df.drop(columns=['Month', 'Day', 'Hour', 'DayOfWeek'])
    
    # ===== STEP 9: DROP REMAINING UNNECESSARY COLUMNS =====
    final_drop_cols = ['Transaction Date', 'Transaction Hour', 'IP Address', 'Customer ID', 'Account Age Days']
    columns_to_drop = [col for col in final_drop_cols if col in df.columns]
    df = df.drop(columns=columns_to_drop, axis=1)
    
    # ===== STEP 10: FEATURE SELECTION (CRITICAL) =====
    if selected_features is not None:
        # Add missing features as 0
        missing_features = list(set(selected_features) - set(df.columns))
        if missing_features:
            df_missing = pd.DataFrame(0, index=df.index, columns=missing_features)
            df = pd.concat([df, df_missing], axis=1)
        
        # Force select only required features in correct order
        # This will silently drop 'Account Age Days' if it wasn't dropped in step 9
        df = df[selected_features]
    
    return df
def transform_bank_fraud_data(raw_data, selected_features=None):
    """
    Transform raw bank account fraud data through all preprocessing steps.
    
    This function applies all the feature engineering and transformations done 
    in the bank-account-fraud.ipynb notebook, including:
    1. Missing value handling and flag creation
    2. Imputation strategies
    3. Ratio and interaction features
    4. Risk scoring features
    5. Categorical encoding
    6. Statistical features (z-scores)
    
    Args:
        raw_data: pandas DataFrame with raw bank account application data
        selected_features: list of feature names to select (optional, for inference)
    
    Returns:
        Transformed pandas DataFrame ready for model prediction
    """
    
    df = raw_data.copy()
    
    # ===== STEP 1: MISSING VALUE HANDLING =====
    missing_cols = [
        "prev_address_months_count",
        "current_address_months_count",
        "intended_balcon_amount",
        "bank_months_count",
        "session_length_in_minutes",
        "device_distinct_emails_8w"
    ]
    
    # Replace -1 with NaN
    for col in missing_cols:
        if col in df.columns:
            df[col] = df[col].replace(-1, np.nan)
    
    # Create missing flags
    for col in missing_cols:
        if col in df.columns:
            df[col + "_missing_flag"] = df[col].isna().astype(int)
    
    # ===== STEP 2: IMPUTATION =====
    if "prev_address_months_count" in df.columns:
        df["prev_address_months_count"] = df["prev_address_months_count"].fillna(0)
    
    if "intended_balcon_amount" in df.columns:
        df["intended_balcon_amount"] = df["intended_balcon_amount"].fillna(0)
    
    if "bank_months_count" in df.columns:
        df["bank_months_count"] = df["bank_months_count"].fillna(0)
        df["new_bank_flag"] = (df["bank_months_count"] == 0).astype(int)
    
    if "session_length_in_minutes" in df.columns:
        median_session = df["session_length_in_minutes"].median()
        df["session_length_in_minutes"] = df["session_length_in_minutes"].fillna(median_session)
    
    if "device_distinct_emails_8w" in df.columns:
        df["device_distinct_emails_8w"] = df["device_distinct_emails_8w"].fillna(0)
    
    # ===== STEP 3: MISSING RISK SCORE =====
    missing_features = [
        "prev_address_months_count_missing_flag",
        "intended_balcon_amount_missing_flag",
        "bank_months_count_missing_flag"
    ]
    existing_missing_features = [col for col in missing_features if col in df.columns]
    if existing_missing_features:
        df["missing_risk_score"] = df[existing_missing_features].sum(axis=1)
    
    # ===== STEP 4: RATIO AND INTERACTION FEATURES =====
    if "proposed_credit_limit" in df.columns and "income" in df.columns:
        df["credit_income_ratio"] = df["proposed_credit_limit"] / (df["income"] + 1)
    
    if "intended_balcon_amount" in df.columns and "income" in df.columns:
        df["balcon_income_ratio"] = df["intended_balcon_amount"] / (df["income"] + 1)
    
    if "credit_risk_score" in df.columns and "proposed_credit_limit" in df.columns:
        df["credit_risk_interaction"] = df["credit_risk_score"] * df["proposed_credit_limit"]
    
    if "income" in df.columns and "customer_age" in df.columns:
        df["income_per_age"] = df["income"] / (df["customer_age"] + 1)
    
    # ===== STEP 5: VELOCITY RATIOS =====
    if "velocity_24h" in df.columns and "velocity_6h" in df.columns:
        df["velocity_ratio_24h_6h"] = df["velocity_24h"] / (df["velocity_6h"] + 1)
        df["velocity_acceleration"] = df["velocity_6h"] - df["velocity_24h"]
    
    if "velocity_4w" in df.columns and "velocity_24h" in df.columns:
        df["velocity_ratio_4w_24h"] = df["velocity_4w"] / (df["velocity_24h"] + 1)
    
    # ===== STEP 6: ADDRESS AND BANK STABILITY =====
    if "current_address_months_count" in df.columns and "prev_address_months_count" in df.columns:
        df["address_stability"] = df["current_address_months_count"] / (df["prev_address_months_count"] + 1)
    
    if "bank_months_count" in df.columns and "customer_age" in df.columns:
        df["bank_age_ratio"] = df["bank_months_count"] / (df["customer_age"] * 12 + 1)
        df["bank_relationship_stability"] = df["bank_months_count"] / (df["customer_age"] * 12 + 1)
    
    # ===== STEP 7: DEVICE AND EMAIL RISK =====
    if "device_fraud_count" in df.columns and "velocity_24h" in df.columns:
        df["device_risk"] = df["device_fraud_count"] * df["velocity_24h"]
    
    if "device_distinct_emails_8w" in df.columns and "velocity_4w" in df.columns:
        df["email_device_ratio"] = df["device_distinct_emails_8w"] / (df["velocity_4w"] + 1)
    
    if "device_distinct_emails_8w" in df.columns and "device_fraud_count" in df.columns:
        df["device_email_ratio"] = df["device_distinct_emails_8w"] / (df["device_fraud_count"] + 1)
    
    # ===== STEP 8: CONTACT VALIDITY SCORE =====
    contact_cols = ["phone_home_valid", "phone_mobile_valid", "email_is_free"]
    if all(col in df.columns for col in contact_cols):
        df["contact_validity_score"] = (
            df["phone_home_valid"] + 
            df["phone_mobile_valid"] + 
            (1 - df["email_is_free"])
        )
    
    # ===== STEP 9: IDENTITY RISK SCORE =====
    identity_risk_cols = ["device_fraud_count", "foreign_request", "date_of_birth_distinct_emails_4w"]
    existing_identity_cols = [col for col in identity_risk_cols if col in df.columns]
    if existing_identity_cols:
        df["identity_risk_score"] = df[existing_identity_cols].sum(axis=1)
    
    # ===== STEP 10: SESSION AND ACTIVITY FEATURES =====
    if "session_length_in_minutes" in df.columns and "velocity_24h" in df.columns:
        df["session_velocity"] = df["session_length_in_minutes"] / (df["velocity_24h"] + 1)
    
    if "velocity_4w" in df.columns and "bank_months_count" in df.columns:
        df["activity_per_month"] = df["velocity_4w"] / (df["bank_months_count"] + 1)
    
    if "bank_branch_count_8w" in df.columns and "velocity_4w" in df.columns:
        df["branch_activity_ratio"] = df["bank_branch_count_8w"] / (df["velocity_4w"] + 1)
    
    # ===== STEP 11: AGE GROUP FEATURES =====
    if "customer_age" in df.columns:
        df["age_group"] = pd.cut(
            df["customer_age"],
            bins=[18, 25, 35, 45, 55, 65, 100],
            labels=False
        )
        
        if "proposed_credit_limit" in df.columns:
            df["credit_per_age_group"] = df.groupby("age_group")["proposed_credit_limit"].transform("mean")
    
    # ===== STEP 12: CATEGORICAL ENCODING =====
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")
    
    # ===== STEP 13: FLAG FEATURES =====
    if "velocity_6h" in df.columns:
        high_velocity_threshold = df["velocity_6h"].quantile(0.95)
        df["high_velocity_flag"] = (df["velocity_6h"] > high_velocity_threshold).astype(int)
    
    if "proposed_credit_limit" in df.columns and "income" in df.columns:
        df["high_credit_flag"] = (df["proposed_credit_limit"] > df["income"] * 2).astype(int)
    
    if "bank_months_count" in df.columns:
        df["new_bank_user_flag"] = (df["bank_months_count"] < 6).astype(int)
    
    if "current_address_months_count" in df.columns:
        df["new_address_flag"] = (df["current_address_months_count"] < 6).astype(int)
    
    # ===== STEP 14: INTERACTION FEATURES =====
    if "credit_risk_score" in df.columns and "income" in df.columns:
        df["credit_risk_income"] = df["credit_risk_score"] * df["income"]
    
    if "velocity_24h" in df.columns and "proposed_credit_limit" in df.columns:
        df["velocity_credit"] = df["velocity_24h"] * df["proposed_credit_limit"]
    
    if "device_fraud_count" in df.columns and "velocity_24h" in df.columns:
        df["device_velocity"] = df["device_fraud_count"] * df["velocity_24h"]
    
    # ===== STEP 15: TEMPORAL FLAGS =====
    if "month" in df.columns:
        df["is_year_start"] = df["month"].isin([1, 2]).astype(int)
        df["is_year_end"] = df["month"].isin([11, 12]).astype(int)
    
    # ===== STEP 16: Z-SCORE FEATURES =====
    if "income" in df.columns:
        income_mean = df["income"].mean()
        income_std = df["income"].std()
        if income_std > 0:
            df["income_zscore"] = (df["income"] - income_mean) / income_std
    
    if "proposed_credit_limit" in df.columns:
        credit_mean = df["proposed_credit_limit"].mean()
        credit_std = df["proposed_credit_limit"].std()
        if credit_std > 0:
            df["credit_zscore"] = (df["proposed_credit_limit"] - credit_mean) / credit_std
    
    # ===== STEP 17: FEATURE SELECTION =====
    if selected_features is not None:
        missing_features = set(selected_features) - set(df.columns)
        for feature in missing_features:
            df[feature] = 0
        df = df[selected_features]
    
    return df



