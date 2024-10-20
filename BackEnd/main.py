from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import numpy as np
from pydantic import BaseModel, HttpUrl
import uvicorn
from typing import List, Dict, Optional
import os
from app.ml.feature_extraction import FeatureExtractor
from app.ml.predictor import Predictor
from app.ml.url_predictor import URLPredictor
from app.ml.model_trainer import ModelTrainer
from app.ml.bulk_feature_extraction import BulkFeatureExtractor
from app.config import settings
from app.logger import setup_logger
from app.exceptions import DataIngestionError, DataTransformationError, PredictionError, ModelTrainerError
from app.ml.data_ingestion_transformation import DataIngestionTransformation  # New import
from sklearn.feature_selection import SelectKBest, f_classif
import pandas as pd
import joblib

logger = setup_logger(__name__)

app = FastAPI(title="Malicious URL Detector", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and Response Models
class URLInput(BaseModel):
    url: HttpUrl

class FeatureOutput(BaseModel):
    features: dict

class PredictionOutput(BaseModel):
    url: str
    prediction: str
    confidence: float
    
class FeatureExtractionInput(BaseModel):
    check_google_index: bool = False

class FeatureExtractionOutput(BaseModel):
    output_file_path: str

class DataIngestionOutput(BaseModel):
    message: str
    train_data_path: str
    test_data_path: str

class DataTransformationOutput(BaseModel):
    message: str
    transformed_train_path: str
    transformed_test_path: str
    preprocessor_path: str

class ModelTrainingOutput(BaseModel):
    message: str
    best_model: str
    best_model_performance: Dict
    all_models_performance: Dict
    best_model_file_path: str
    comparison_plot_path: str
    confusion_matrix_path: str
    classification_report: str

# Dependency Injection
def get_bulk_extractor():
    return BulkFeatureExtractor()


def get_model_trainer():
    return ModelTrainer()

def get_data_ingestion_transformation():
    return DataIngestionTransformation()

def get_url_predictor():
    return URLPredictor()



def get_feature_extractor():
    return FeatureExtractor()

@app.get("/")
async def root():
    return {"message": "Welcome to the Malicious URL Detector API"}

# New API endpoint for data ingestion and transformation
@app.post("/api/ingest_transform_data", response_model=Dict[str, str])
async def ingest_transform_data(
    data_ingestion_transformation: DataIngestionTransformation = Depends(get_data_ingestion_transformation),
    custom_file: UploadFile = File(None)
):
    try:
        custom_file_path = None
        if custom_file:
            # Save the uploaded file temporarily
            custom_file_path = os.path.join(settings.EXTRACTED_DATA, f"custom_{custom_file.filename}")
            with open(custom_file_path, "wb") as buffer:
                content = await custom_file.read()
                buffer.write(content)
        
        train_arr, test_arr, preprocessor_file = data_ingestion_transformation.initiate_data_ingestion_transformation(custom_file_path)
        
        if custom_file_path:
            os.remove(custom_file_path)  # Clean up the temporary file
        
        return {
            "message": "Data ingestion and transformation completed successfully",
            "train_data_path": data_ingestion_transformation.train_data_path,
            "test_data_path": data_ingestion_transformation.test_data_path,
            "preprocessor_file_path": preprocessor_file
        }
    except Exception as e:
        logger.error(f"Error in data ingestion and transformation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/extract_features", response_model=FeatureExtractionOutput)
async def extract_features(
    file: UploadFile = File(None),
    check_google_index: bool = Form(False),
    bulk_extractor: BulkFeatureExtractor = Depends(get_bulk_extractor)
):
    try:
        output_file = await bulk_extractor.extract_features_from_csv(check_google_index, file)
        return FeatureExtractionOutput(output_file_path=output_file)
    except Exception as e:
        logger.error(f"Error in feature extraction: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/train_model")
async def train_model(
    model_trainer: ModelTrainer = Depends(get_model_trainer),
    data_ingestion_transformation: DataIngestionTransformation = Depends(get_data_ingestion_transformation)
):
    try:
        # Load the transformed data
        train_path = os.path.join(settings.TRAIN_DATA_DIR, "transformed_train_data.csv")
        test_path = os.path.join(settings.TEST_DATA_DIR, "transformed_test_data.csv")

        if not os.path.exists(train_path) or not os.path.exists(test_path):
            raise HTTPException(status_code=400, detail="Transformed data not found. Please run data transformation first.")

        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        # Split features and target
        X_train = train_df.drop('label', axis=1)
        y_train = train_df['label']
        X_test = test_df.drop('label', axis=1)
        y_test = test_df['label']

        # Feature Selection using SelectKBest
        selector = SelectKBest(score_func=f_classif, k=13)  # Select top 13 features
        X_train_selected = selector.fit_transform(X_train, y_train)
        X_test_selected = selector.transform(X_test)

        # Get the selected feature names
        selected_features = X_train.columns[selector.get_support()].tolist()
        logger.info(f"Selected Features: {selected_features}")

        # Initiate model training
        best_model = model_trainer.initiate_model_training(X_train_selected, y_train, X_test_selected, y_test)

        # Save selected features
        preprocessor_file_path = os.path.join(settings.PREPROCESSOR_MODEL_DIR, settings.PREPROCESSOR_FILENAME)
        preprocessor_dict = {"features": selected_features}
        with open(preprocessor_file_path, 'wb') as f:
            joblib.dump(preprocessor_dict, f)
        logger.info(f"Saved selected features to {preprocessor_file_path}")

        return {
            "message": "Model training completed successfully",
            "best_model": best_model['Model Name'],
            "best_model_accuracy": best_model['accuracy'],
            "best_model_precision": best_model['precision'],
            "best_model_recall": best_model['recall'],
            "best_model_f1_score": best_model['f1_score'],
            "selected_features": selected_features,
            "best_model_file_path": os.path.join(settings.READY_MODEL_DIR, f"{best_model['Model Name']}.pkl")
        }
    except ModelTrainerError as e:
        logger.error(f"Error in model training: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in model training: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during model training")

@app.post("/api/predict_url", response_model=PredictionOutput)
async def predict_url(url_input: URLInput, url_predictor: URLPredictor = Depends(get_url_predictor)):
    try:
        prediction_result = url_predictor.predict(str(url_input.url))
        
        return PredictionOutput(
            url=str(url_input.url),
            prediction=prediction_result["result"],
            confidence=prediction_result["confidence"]
        )
    except PredictionError as e:
        logger.error(f"Error in URL prediction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in URL prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during prediction")



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)