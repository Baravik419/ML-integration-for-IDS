import joblib
import pandas as pd

Categorical_Columns = [
    "src_ip",
    "dst_ip",
    "proto",
    "service",
    "conn_state"
]

def load_model_data():
    x_columns = joblib.load("Models/XGBoost_Model_Integration (5 fold)/XGB_Integration_X_columns.pkl")
    scaler = joblib.load("Models/XGBoost_Model_Integration (5 fold)/XGB_Integration_scaler.pkl")
    ordinal_encoder = joblib.load("Models/XGBoost_Model_Integration (5 fold)/XGB_Integration_Ordinal_Encoder.pkl")

    return x_columns, scaler, ordinal_encoder

def features_to_dataframe(features: dict, x_columns: list) -> pd.DataFrame:
    df = pd.DataFrame([features])

    for column in x_columns:
        if column not in df.columns:
            df[column] = 0

    df = df[x_columns]
    return df

def encode_categorical_columns(df: pd.DataFrame, ordinal_encoder) -> pd.DataFrame:
    df = df.copy()
    df[Categorical_Columns] = ordinal_encoder.transform(df[Categorical_Columns])
    return df

def scale_features(df: pd.DataFrame, scaler) -> pd.DataFrame:
    scaled = scaler.transform(df)
    return pd.DataFrame(scaled, columns=df.columns, index=df.index)

def prepare_features_for_inference(features: dict) -> pd.DataFrame:
    x_columns, scaler, ordinal_encoder = load_model_data()

    df = features_to_dataframe(features, x_columns)
    df = encode_categorical_columns(df, ordinal_encoder)
    df = scale_features(df, scaler)

    return df

