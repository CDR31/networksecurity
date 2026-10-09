import sys
import os

# Ensure the project root is available when this file is launched from elsewhere.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import certifi
ca = certifi.where()
from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
print(mongo_db_url)
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,File,UploadFile,Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel # pyright: ignore[reportMissingImports]

client = pymongo.MongoClient(mongo_db_url,tlsCAFILE = ca)
from networksecurity.constant.training_pipeline import DATA_INGESTION_COLLECTION_NAME
from networksecurity.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
# templates = Jinja2Templates(directory="./templates")
templates = Jinja2Templates(directory="template")

@app.get("/",tags=['authentication'])
async def index():
    return RedirectResponse(url = "/docs")

@app.get("/train")
async def train_route():
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful.")
    except Exception as e:
        raise NetworkSecurityException(e,sys)

@app.post("/predict")
async def predict_route(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        # Validate the uploaded file
        if not file.filename or not file.filename.lower().endswith(".csv"):
            return Response(
                content="Please upload a valid CSV file.",
                status_code=400
            )

        # Read the uploaded CSV
        df = pd.read_csv(file.file)

        if df.empty:
            return Response(
                content="The uploaded CSV file is empty.",
                status_code=400
            )

        # Load the trained model and preprocessor
        preprocessor = load_object("final_models/preprocessor.pkl")
        final_model = load_object("final_models/model.pkl")

        network_model = NetworkModel(
            preprocessor=preprocessor,
            model=final_model
        )

        # Generate predictions
        y_pred = network_model.predict(df)

        # Add predictions to the dataframe
        df["predicted_column"] = y_pred

        # Save prediction results
        os.makedirs("prediction_output", exist_ok=True)

        df.to_csv(
            "prediction_output/output.csv",
            index=False
        )

        # Convert results into an HTML table
        table_html = df.to_html(
            index=False,
            classes="table table-striped"
        )

        return templates.TemplateResponse(
            request=request,
            name="table.html",
            context={"table": table_html}
        )

    except Exception as e:
        logging.exception("Prediction failed")

        raise NetworkSecurityException(e, sys)

    finally:
        await file.close()

if __name__=="__main__":
    app_run(app,host="localhost",port = 8000)