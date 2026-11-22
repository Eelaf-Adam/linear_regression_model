# SouqCast: Predicting Wartime Food Prices in Sudanese Markets

## Mission and problem
**My mission:** is to build localized, low-resource AI that addresses aid reach Sudanese families fairly during the war.

**Problem:** Since the war began in April 2023, food prices in Sudan differ sharply between markets and months, which makes it hard for aid agencies to set fair cash-transfer amounts.

**SouqCast:** predicts the retail price of a food item (USD per kg) for a given market and month, so cash support can match real local prices.

## Dataset
WFP Sudan food prices, published by the World Food Programme on the Humanitarian Data Exchange (HDX):
https://data.humdata.org/dataset/wfp-food-prices-for-sudan

Monthly market prices for 23,384 records (16 columns) from 2001 to 2026. The model uses the war period from 15 April 2023: 6,961 food prices across 19 markets and 13 foods, converted to USD per kg.

## API (Swagger UI)
https://sudan-food-price-api.onrender.com/docs

- `POST /predict` returns the predicted price for 9 inputs
- `POST /retrain` takes a CSV of new WFP data and retrains the model on the original data plus the new rows

The free Render plan sleeps after 15 minutes, so the first request can take up to a minute.

## Video demo
[YouTube link: https://youtu.be/SVg712QUOAs]

## Run the mobile app
1. Install Flutter (3.x) and connect an Android phone with USB debugging on, or start an Android emulator.
2. Clone the repository:
   ```
   git clone https://github.com/Eelaf-Adam/linear_regression_model.git
   ```
3. Go to the app folder:
   ```
   cd linear_regression_model/summative/FlutterApp
   ```
4. Install the packages:
   ```
   flutter pub get
   ```
5. Check your device is listed, then run the app:
   ```
   flutter devices
   flutter run
   ```
6. Fill in the 9 fields (e.g. Damazin, Blue Nile, 11.79, 34.36, cereals and tubers, Sorghum, Retail, 2024, 3) and press Predict.

## Project structure
```
linear_regression_model/
├── README.md                        
└── summative/
    ├── pyproject.toml               # Python packages for the notebook (uv)
    ├── uv.lock                      # exact package versions for the notebook
    ├── linear_regression/
    │   ├── multivariate.ipynb       # data exploration, 4 models, best model saved
    │   └── wfp_food_prices_sdn.csv  # dataset used by the notebook and by /retrain
    ├── API/
    │   ├── prediction.py            # FastAPI app: /predict, /retrain, CORS, input checks
    │   ├── retrain.py               # cleans new data, refits the model on old + new rows
    │   ├── pyproject.toml           # API packages, installed by Render
    │   ├── uv.lock                  # exact package versions for the API
    │   └── best_model.pkl           # saved pipeline (preprocessing + Random Forest)
    └── FlutterApp/                  # SouqCast mobile app (lib/main.dart)
```
