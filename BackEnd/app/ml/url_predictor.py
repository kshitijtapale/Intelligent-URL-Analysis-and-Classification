import os
import numpy as np
import pandas as pd
import joblib
from app.config import settings
from app.exceptions import PredictionError
from app.logger import setup_logger
from app.ml.feature_extraction import FeatureExtractor

logger = setup_logger(__name__)

class URLPredictor:
    def __init__(self):
        self.model_file_path = os.path.join(settings.READY_MODEL_DIR, settings.MODEL_FILENAME)
        self.preprocessor_file_path = os.path.join(settings.PREPROCESSOR_MODEL_DIR, settings.PREPROCESSOR_FILENAME)
        self.feature_extractor = FeatureExtractor()
        self.model, self.selected_features = self.load_model_and_features()

    def load_model_and_features(self):
        try:
            model = joblib.load(self.model_file_path)
            with open(self.preprocessor_file_path, 'rb') as f:
                preprocessor_dict = joblib.load(f)
            selected_features = preprocessor_dict.get("features", [])
            logger.info(f"Loaded {len(selected_features)} selected features: {selected_features}")
            return model, selected_features
        except Exception as e:
            logger.error(f"Exception occurred in loading model and features: {e}")
            raise PredictionError(f"Error occurred in loading model and features: {str(e)}")

    def preprocess_url(self, url: str) -> pd.DataFrame:
        all_features = self.feature_extractor.extract_features(url, 0)  # 0 is a placeholder for the label
        df = pd.DataFrame([all_features])
        
        # Filter only the selected features
        filtered_df = df[self.selected_features]
        logger.info(f"Preprocessed URL features shape: {filtered_df.shape}")
        return filtered_df

    def predict(self, url: str) -> dict:
        try:
            processed_data = self.preprocess_url(url)
            prediction = self.model.predict(processed_data)[0]
            prediction_proba = self.model.predict_proba(processed_data)[0]
            
            result = "BEWARE MALICIOUS WEBSITE" if prediction == 1 else "SAFE WEBSITE"
            confidence = prediction_proba[1] if prediction == 1 else prediction_proba[0]
            
            return {
                "result": result,
                "confidence": float(confidence)
            }
        except Exception as e:
            logger.error(f"Error in URL prediction: {str(e)}")
            raise PredictionError(f"Error in URL prediction: {str(e)}")