import mlflow 
import uvicorn
import json
import pandas as pd 
from pydantic import BaseModel
from typing import Literal, List, Union
from fastapi import FastAPI, File, UploadFile
import pickle

description = """
Get around API helps drivers choose the right price for their car rental. 

The goal of this API is to suggest prices for daily car rentals to owners based on their car specifications such as type of fuel, 
mileage, etc...

## Machine-Learning 

Where you can:
* `/predict` Predict the ideal rental price per day for a car
* `/batch-predict` where you can upload a file to get predictions for several vehicles


Check out documentation for more information on each endpoint. 
"""

tags_metadata = [
    {
        "name": "Machine-Learning",
        "description": "Endpoints that predict rental price per day"
    }]

app = FastAPI(
    title="GetAround API",
    description=description,
    version="0.1",
    openapi_tags=tags_metadata
)

class PredictionFeatures(BaseModel):
    model_key : str
    mileage: int
    engine_power: int
    fuel: str
    paint_color: str
    car_type: str
    private_parking_available: bool
    has_gps: bool
    has_air_conditioning: bool
    automatic_car: bool
    has_getaround_connect: bool
    has_speed_regulator: bool
    winter_tires: bool

@app.post('/predict', tags=["Machine-Learning"])

async def predict(predictionFeatures: PredictionFeatures):
    """
    Make a prediction on an observation.

    You can use this as an example: 

    {
      "model_key": "Citroën",
      "mileage": 140411,
      "engine_power": 100,
      "fuel": "diesel",
      "paint_color": "black",
      "car_type": "convertible",
      "private_parking_available": true,
      "has_gps": true,
      "has_air_conditioning": true,
      "automatic_car": true,
      "has_getaround_connect": true,
      "has_speed_regulator": true,
      "winter_tires": true
    }
    """
    
    df = pd.DataFrame(dict(predictionFeatures), index=[0])
    

    loaded_model = pickle.load(open('model.pkl', 'rb'))

    prediction = loaded_model.predict(df)

    response = {"prediction": prediction.tolist()[0]}
    return response

@app.post("/batch-predict", tags=["Machine-Learning"])
async def batch_predict(file: UploadFile = File(...)):
    """
    Make prediction on a batch of observations. This endpoint accepts only **csv files** containing 
    all the columns WITHOUT the target variable. 
    """
    # Read file 
    df = pd.read_csv(file.file)

    loaded_model = pickle.load(open('model.pkl', 'rb'))

    predictions = loaded_model.predict(df)

    return predictions.tolist()

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)