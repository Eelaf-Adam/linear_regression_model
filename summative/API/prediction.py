from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from retrain import retrain_model

MODEL_PATH = Path(__file__).parent / "best_model.pkl"

app = FastAPI(
    title="Sudan Food Price Prediction API",
    description="Predicts the retail price of food (USD per kg) in Sudanese markets during the war.",
)

# CORS: only the browser sites below may call this API, never "*".
# - allow_origins: our Render site and the local Flutter web build (port 5000). Other sites
#   cannot use the model, so nobody can show aid agencies made-up prices through it.
# - allow_methods: GET and POST only. Nothing is edited or deleted, so PUT/DELETE are blocked.
# - allow_headers: Content-Type only, because the app sends plain JSON and nothing else.
# - allow_credentials: False, since there are no logins or cookies.
# The Flutter mobile app is not a browser, so CORS does not restrict it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sudan-food-price-api.onrender.com",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

model = joblib.load(MODEL_PATH)

# allowed values, taken from the war-period training data
Market = Literal[
    "Al Fashir", "Damazin", "Dongola", "Ed Damer", "Eddein", "El Fula", "El Gedarif",
    "El Geneina", "El Obeid", "Kadugli", "Kassala", "Khartoum", "Kosti", "Nyala El Kabeer",
    "Port Sudan", "Singa", "Tawila", "Wad Medani", "Zalingi",
]
State = Literal[
    "Al Gezira", "Blue Nile", "Central Darfur", "Eastern Darfur", "Gedaref", "Kassala",
    "Khartoum", "Nile", "North Darfur", "North Kordofan", "Northern", "Red Sea", "Sennar",
    "South Darfur", "South Kordofan", "West Darfur", "West Kordofan", "White Nile",
]
Category = Literal[
    "cereals and tubers", "meat, fish and eggs", "milk and dairy", "miscellaneous food",
    "oil and fats", "pulses and nuts", "vegetables and fruits",
]
Commodity = Literal[
    "Beans (fava, egyptian)", "Meat (beef)", "Meat (goat)", "Milk (powder)", "Millet",
    "Oil (vegetable)", "Onions", "Salt (iodised)", "Sorghum", "Sorghum (food aid)", "Sugar",
    "Tomatoes (dried)", "Wheat flour",
]

# each market belongs to one state and each food to one category in the data
MARKET_STATE = {
    "Al Fashir": "North Darfur", "Damazin": "Blue Nile", "Dongola": "Northern",
    "Ed Damer": "Nile", "Eddein": "Eastern Darfur", "El Fula": "West Kordofan",
    "El Gedarif": "Gedaref", "El Geneina": "West Darfur", "El Obeid": "North Kordofan",
    "Kadugli": "South Kordofan", "Kassala": "Kassala", "Khartoum": "Khartoum",
    "Kosti": "White Nile", "Nyala El Kabeer": "South Darfur", "Port Sudan": "Red Sea",
    "Singa": "Sennar", "Tawila": "North Darfur", "Wad Medani": "Al Gezira",
    "Zalingi": "Central Darfur",
}
MARKET_COORDS = {
    "Al Fashir": (13.63, 25.35), "Damazin": (11.79, 34.36), "Dongola": (19.17, 30.47),
    "Ed Damer": (17.58, 33.97), "Eddein": (11.43, 26.15), "El Fula": (11.73, 28.36),
    "El Gedarif": (14.04, 35.38), "El Geneina": (13.45, 22.45), "El Obeid": (13.19, 30.22),
    "Kadugli": (11.02, 29.72), "Kassala": (15.46, 36.40), "Khartoum": (15.51, 32.54),
    "Kosti": (13.17, 32.67), "Nyala El Kabeer": (12.05, 24.88), "Port Sudan": (19.62, 37.22),
    "Singa": (13.14, 33.93), "Tawila": (13.52, 24.86), "Wad Medani": (14.40, 33.52),
    "Zalingi": (12.90, 23.48),
}
COMMODITY_CATEGORY = {
    "Beans (fava, egyptian)": "pulses and nuts", "Meat (beef)": "meat, fish and eggs",
    "Meat (goat)": "meat, fish and eggs", "Milk (powder)": "milk and dairy",
    "Millet": "cereals and tubers", "Oil (vegetable)": "oil and fats",
    "Onions": "vegetables and fruits", "Salt (iodised)": "miscellaneous food",
    "Sorghum": "cereals and tubers", "Sorghum (food aid)": "cereals and tubers",
    "Sugar": "miscellaneous food", "Tomatoes (dried)": "vegetables and fruits",
    "Wheat flour": "cereals and tubers",
}


class PriceInput(BaseModel):
    model_config = ConfigDict(strict=True)  # no silent conversions, e.g. "2024" is rejected for year

    market: Market = Field(..., description="Market town", examples=["Damazin"])
    admin1: State = Field(..., description="State the market is in", examples=["Blue Nile"])
    category: Category = Field(..., description="Food group", examples=["cereals and tubers"])
    commodity: Commodity = Field(..., description="Food item", examples=["Sorghum"])
    pricetype: Literal["Retail"] = Field(..., description="Always Retail in the war data", examples=["Retail"])
    latitude: float = Field(..., ge=8.0, le=23.0, description="Market latitude, Sudan spans about 8 to 23", examples=[11.79])
    longitude: float = Field(..., ge=21.0, le=39.0, description="Market longitude, Sudan spans about 21 to 39", examples=[34.36])
    year: int = Field(..., ge=2023, le=2030, description="Year, from the war start (2023) to 2030", examples=[2024])
    month: int = Field(..., ge=1, le=12, description="Month, 1 to 12", examples=[3])


class PriceOutput(BaseModel):
    predicted_price_usd_per_kg: float
    model_config = ConfigDict(strict=True)


@app.get("/")
def home():
    return {"message": "Sudan food price API. Go to /docs to test it."}


@app.post("/predict", response_model=PriceOutput)
def predict(data: PriceInput):
    # each value can be valid alone but wrong together, e.g. Damazin with Khartoum state
    state = MARKET_STATE[data.market]
    if data.admin1 != state:
        raise HTTPException(status_code=422, detail=f"{data.market} is in {state} state, not {data.admin1}.")
    lat, lon = MARKET_COORDS[data.market]
    if abs(data.latitude - lat) > 0.01 or abs(data.longitude - lon) > 0.01:
        raise HTTPException(status_code=422, detail=f"{data.market} is at latitude {lat}, longitude {lon}.")
    category = COMMODITY_CATEGORY[data.commodity]
    if data.category != category:
        raise HTTPException(status_code=422, detail=f"{data.commodity} belongs to {category}, not {data.category}.")
    try:
        row = pd.DataFrame([data.model_dump()])
        price = model.predict(row)[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
    return {"predicted_price_usd_per_kg": round(float(price), 2)}


@app.post("/retrain")
def retrain(file: UploadFile = File(..., description="CSV with the same columns as the WFP Sudan food prices data")):
    """Upload new WFP price data as CSV. The upload alone retrains the model on the original
    data plus the new rows, and /predict uses the updated model straight away."""
    global model
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    try:
        new_df = pd.read_csv(file.file)
        new_model, summary = retrain_model(new_df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {e}")
    model = new_model  # /predict uses the new model from now on
    return {"message": "Model retrained on the original data plus the new rows.", **summary}
