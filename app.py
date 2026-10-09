import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import certifi
import pandas as pd
import pymongo

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel


# ---------------------------------------------------------
# 1. Project configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# Ensure project root is available for imports.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables from the project root.
load_dotenv(BASE_DIR / ".env")

# Use the same variable name throughout the project.
MONGO_DB_URL = os.getenv("MONGO_DB_URL")

# Model artifacts.
MODEL_PATH = BASE_DIR / "final_models" / "model.pkl"
PREPROCESSOR_PATH = BASE_DIR / "final_models" / "preprocessor.pkl"

# Prediction output directory.
PREDICTION_OUTPUT_DIR = BASE_DIR / "prediction_output"

# HTML templates.
TEMPLATE_DIR = BASE_DIR / "template"


# ---------------------------------------------------------
# 2. Optional MongoDB client
# ---------------------------------------------------------

mongo_client = None


def get_mongodb_client():
    """
    Create and verify a MongoDB Atlas connection when needed.

    MongoDB is not contacted automatically when app.py
    is imported.
    """
    global mongo_client

    if not MONGO_DB_URL:
        raise RuntimeError(
            "MONGO_DB_URL is missing. "
            "Configure it in your .env file or deployment settings."
        )

    if mongo_client is None:
        client = pymongo.MongoClient(
            MONGO_DB_URL,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=15000,
        )

        try:
            client.admin.command("ping")
        except Exception:
            client.close()
            raise

        mongo_client = client
        logging.info("MongoDB Atlas connection successful.")

    return mongo_client


# ---------------------------------------------------------
# 3. FastAPI application
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Database connections are not required merely to start
    the prediction API. They are opened when needed.
    """
    yield

    global mongo_client

    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None


app = FastAPI(
    title="Network Security ML API",
    description=(
        "API for training a network security classification "
        "model and generating predictions from CSV files."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# 4. CORS configuration
# ---------------------------------------------------------

# Configure ALLOWED_ORIGINS as a comma-separated environment
# variable if a frontend needs to call this API.
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Wildcard is convenient for local testing.
# For production, configure explicit frontend origins.
if not allowed_origins:
    allowed_origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# 5. HTML templates
# ---------------------------------------------------------

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ---------------------------------------------------------
# 6. Home endpoint
# ---------------------------------------------------------

@app.get("/", tags=["General"])
async def index():
    """
    Redirect users to FastAPI documentation.
    """
    return RedirectResponse(url="/docs")


# ---------------------------------------------------------
# 7. Health endpoint
# ---------------------------------------------------------

@app.get("/health", tags=["General"])
async def health_check():
    """
    Check whether the API process is responding.

    This does not guarantee that MongoDB is reachable
    or that model artifacts are valid.
    """
    return {
        "status": "healthy",
        "service": "Network Security ML API",
    }


# ---------------------------------------------------------
# 8. Training endpoint
# ---------------------------------------------------------

@app.post("/train", tags=["Training"])
async def train_route():
    """
    Execute the existing training pipeline.

    For production, protect this endpoint with authentication
    or move training into a separate background job.
    """
    try:
        logging.info("Network Security training started.")

        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()

        logging.info("Network Security training completed.")

        return {
            "status": "success",
            "message": "Training pipeline completed successfully.",
        }

    except Exception as e:
        logging.exception("Training pipeline failed.")

        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}",
        ) from e


# ---------------------------------------------------------
# 9. Prediction endpoint
# ---------------------------------------------------------

@app.post("/predict", tags=["Prediction"])
async def predict_route(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Accept a CSV file, load the trained model and preprocessor,
    generate predictions, save the output CSV, and display
    the results as an HTML table.
    """

    try:
        # Validate the uploaded file.
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid CSV file.",
            )

        # Read the CSV.
        try:
            df = pd.read_csv(file.file)
        except (pd.errors.ParserError, UnicodeDecodeError) as e:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid readable CSV.",
            ) from e

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV file is empty.",
            )

        # Remove accidental whitespace from column names.
        df.columns = df.columns.astype(str).str.strip()

        if df.columns.duplicated().any():
            raise HTTPException(
                status_code=400,
                detail="The CSV contains duplicate column names.",
            )

        # Verify that the trained artifacts exist.
        if not MODEL_PATH.is_file():
            raise HTTPException(
                status_code=503,
                detail=(
                    "The trained model was not found. "
                    "Run the training pipeline first."
                ),
            )

        if not PREPROCESSOR_PATH.is_file():
            raise HTTPException(
                status_code=503,
                detail=(
                    "The preprocessor was not found. "
                    "Run the training pipeline first."
                ),
            )

        # Load the trained model and preprocessor.
        preprocessor = load_object(str(PREPROCESSOR_PATH))
        final_model = load_object(str(MODEL_PATH))

        network_model = NetworkModel(
            preprocessor=preprocessor,
            model=final_model,
        )

        # Generate predictions.
        # NetworkModel.predict must apply the preprocessing
        # expected by the saved model.
        y_pred = network_model.predict(df)

        if len(y_pred) != len(df):
            raise RuntimeError(
                "The number of predictions does not match "
                "the number of input rows."
            )

        # Add predictions to the original dataframe.
        result_df = df.copy()
        result_df["predicted_column"] = y_pred

        # Save prediction results.
        PREDICTION_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = PREDICTION_OUTPUT_DIR / "output.csv"

        result_df.to_csv(
            output_path,
            index=False,
        )

        logging.info(
            "Prediction completed for %s rows.",
            len(result_df),
        )

        # Render the results as an HTML table.
        if not (TEMPLATE_DIR / "table.html").is_file():
            raise HTTPException(
                status_code=500,
                detail=(
                    "The prediction template is missing. "
                    "Check template/table.html."
                ),
            )

        table_html = result_df.to_html(
            index=False,
            classes="table table-striped",
            escape=True,
        )

        return templates.TemplateResponse(
            request=request,
            name="table.html",
            context={
                "table": table_html,
                "prediction_count": len(result_df),
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        logging.exception("Prediction failed.")

        raise HTTPException(
            status_code=500,
            detail=(
                "Prediction failed. Check the application logs "
                "for the underlying error."
            ),
        ) from e

    finally:
        await file.close()


# ---------------------------------------------------------
# 10. Run locally
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )

