from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import numpy as np
import pandas as pd
from pydantic import BaseModel, HttpUrl, confloat
import uvicorn
from typing import List, Dict, Optional, Any, Tuple
import os
from app.ml.feature_extraction import FeatureExtractor
from app.ml.url_predictor import URLPredictor
from app.ml.model_trainer import ModelTrainer
from app.ml.bulk_feature_extraction import BulkFeatureExtractor
from app.ml.adaptive_learner import AdaptiveLearner
from app.config import settings
from app.logger import setup_logger
from app.exceptions import DataIngestionError, DataTransformationError, PredictionError, ModelTrainerError
from app.ml.data_ingestion_transformation import DataIngestionTransformation
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Depends
from app.models.url_feedback import init_db, get_db
from app.models.init_db import create_database


logger = setup_logger(__name__)

app = FastAPI(title="Malicious URL Detector", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    try:
        # Create database if it doesn't exist
        create_database()
        # Initialize tables
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
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

class PredictionOutput(BaseModel):
    url: str
    prediction: str
    confidence: float
    feature_contributions: Dict[str, float]
    top_indicators: List[Tuple[str, float]]

class ModelTrainingOutput(BaseModel):
    message: str
    best_model: str
    best_model_performance: Dict[str, float]
    all_models_performance: Dict[str, Dict[str, float]]
    selected_features: List[str]
    best_model_file_path: str

# Update the response models
   
class ModelPerformance(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float

class ModelTrainingResponse(BaseModel):
    message: str
    best_model: str
    model_performance: ModelPerformance
    selected_features: List[str]
    best_model_file_path: str
    all_models_performance: Dict[str, ModelPerformance]

class FeedbackInput(BaseModel):
    url: HttpUrl
    is_malicious: bool
    confidence: confloat(ge=0.0, le=1.0)

def get_adaptive_learner():
    return AdaptiveLearner()

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
        train_path = os.path.join(settings.TRAIN_DATA_DIR, "transformed_train_data.csv")
        test_path = os.path.join(settings.TEST_DATA_DIR, "transformed_test_data.csv")

        if not os.path.exists(train_path) or not os.path.exists(test_path):
            raise HTTPException(
                status_code=400,
                detail="Transformed data not found. Please run data transformation first."
            )

        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        X_train = train_df.drop('label', axis=1)
        y_train = train_df['label']
        X_test = test_df.drop('label', axis=1)
        y_test = test_df['label']

        training_results = model_trainer.initiate_model_training(X_train, y_train, X_test, y_test)

        return {
            "message": training_results["message"],
            "best_model": training_results["best_model"],
            "model_performance": training_results["model_performance"],
            "selected_features": training_results["selected_features"],
            "best_model_file_path": training_results["best_model_file_path"],
            "all_models_performance": training_results["all_models_performance"]
        }

    except Exception as e:
        logger.error(f"Unexpected error in model training: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during model training: {str(e)}"
        )


@app.post("/api/predict_url", response_model=Dict[str, Any])
async def predict_url(
    url_input: URLInput,
    url_predictor: URLPredictor = Depends(get_url_predictor)
):
    try:
        prediction_result = url_predictor.predict(str(url_input.url))
        return prediction_result
    except Exception as e:
        logger.error(f"Unexpected error in URL prediction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during prediction: {str(e)}"
        )

@app.post("/api/feedback")
async def process_feedback(
    feedback: FeedbackInput,
    db: Session = Depends(get_db),
    adaptive_learner: AdaptiveLearner = Depends(get_adaptive_learner)
):
    try:
        result = await adaptive_learner.process_feedback(
            str(feedback.url),
            feedback.is_malicious,
            feedback.confidence,
            db
        )
        return result
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )
        
@app.post("/api/retrain")
async def retrain_model(
    db: Session = Depends(get_db),
    adaptive_learner: AdaptiveLearner = Depends(get_adaptive_learner)
):
    try:
        result = await adaptive_learner.retrain_model(db)
        return result
    except Exception as e:
        logger.error(f"Error retraining model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retraining model: {str(e)}"
        )
        
@app.get("/api/training_stats")
async def get_training_stats(
    db: Session = Depends(get_db),
    adaptive_learner: AdaptiveLearner = Depends(get_adaptive_learner)
):
    try:
        stats = await adaptive_learner.get_training_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting training stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting training stats: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)