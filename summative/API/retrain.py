from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

LOCAL_DATA = Path(__file__).parent.parent / "linear_regression" / "wfp_food_prices_sdn.csv"
DATA_URL = "https://raw.githubusercontent.com/Eelaf-Adam/linear_regression_model/main/summative/linear_regression/wfp_food_prices_sdn.csv"

CATEGORICAL = ["market", "admin1", "category", "commodity", "pricetype"]
NUMERIC = ["latitude", "longitude", "year", "month"]
REQUIRED = ["date", "unit", "usdprice", "market", "admin1", "category", "commodity", "pricetype", "latitude", "longitude"]


def load_original():
    # local file on the laptop, GitHub copy on Render
    if LOCAL_DATA.exists():
        return pd.read_csv(LOCAL_DATA)
    return pd.read_csv(DATA_URL)


def kg_in_unit(unit):
    if unit in ("KG", "L"):
        return 1.0
    return float(unit.split()[0])


def clean(df):
    # same steps as the notebook
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2023-04-15"]
    df = df[df["category"] != "non-food"]
    df["usd_per_kg"] = df["usdprice"] / df["unit"].apply(kg_in_unit)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def retrain_model(new_df):
    missing = [c for c in REQUIRED if c not in new_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    original = clean(load_original())
    new = clean(new_df)
    if new.empty:
        raise ValueError("No usable rows: new data must be food prices from 15 April 2023 onward.")

    # if a price is in both files, keep the new one
    data = pd.concat([original, new], ignore_index=True)
    data = data.drop_duplicates(subset=["date", "market", "commodity", "unit"], keep="last")

    X = data[CATEGORICAL + NUMERIC]
    y = data["usd_per_kg"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ("preprocess", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("num", StandardScaler(), NUMERIC),
        ])),
        ("model", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)

    # names the model learned that /predict does not accept yet
    new_values = {}
    for col in ["market", "admin1", "category", "commodity"]:
        unseen = sorted(set(new[col]) - set(original[col]))
        if unseen:
            new_values[col] = unseen

    summary = {
        "original_rows": len(original),
        "new_rows": len(new),
        "rows_used": len(data),
        "test_mse": round(float(mean_squared_error(y_test, pred)), 2),
        "test_mae": round(float(mean_absolute_error(y_test, pred)), 2),
        "new_values_not_in_predict_lists": new_values,
    }
    return pipeline, summary
