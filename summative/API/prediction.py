from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

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
    try:
        row = pd.DataFrame([data.model_dump()])
        price = model.predict(row)[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
    return {"predicted_price_usd_per_kg": round(float(price), 2)}
