import os
import numpy as np
import pandas as pd
import joblib
from app.config import settings
from app.exceptions import PredictionError
from app.logger import setup_logger
from app.ml.feature_extraction import FeatureExtractor
from typing import List, Dict
logger = setup_logger(__name__)

class URLPredictor:
    def __init__(self):
        self.model_file_path = os.path.join(settings.READY_MODEL_DIR, settings.MODEL_FILENAME)
        self.preprocessor_file_path = os.path.join(settings.PREPROCESSOR_MODEL_DIR, settings.PREPROCESSOR_FILENAME)
        self.feature_extractor = FeatureExtractor()
        self.model_data = self.load_model_and_features()
        self.model = self.model_data['model']
        self.feature_columns = self.model_data['feature_columns']
        self.scaler = self.load_preprocessor()['scaler']

    def load_model_and_features(self) -> dict:
        try:
            model_data = joblib.load(self.model_file_path)
            logger.info(f"Loaded model with {len(model_data['feature_columns'])} features")
            return model_data
        except Exception as e:
            logger.error(f"Exception occurred in loading model: {e}")
            raise PredictionError(f"Error loading model: {str(e)}")

    def load_preprocessor(self) -> dict:
        try:
            with open(self.preprocessor_file_path, 'rb') as f:
                return joblib.load(f)
        except Exception as e:
            logger.error(f"Error loading preprocessor: {e}")
            raise PredictionError(f"Error loading preprocessor: {str(e)}")

    def preprocess_url(self, url: str) -> pd.DataFrame:
        try:
            features = self.feature_extractor.extract_features(url)
            df = pd.DataFrame([features])
            
            # Ensure all required features are present
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0
            
            # Select only the required features in the correct order
            df = df[self.feature_columns]
            
            # Scale features
            df_scaled = pd.DataFrame(
                self.scaler.transform(df),
                columns=self.feature_columns
            )
            
            return df_scaled
            
        except Exception as e:
            logger.error(f"Error in URL preprocessing: {str(e)}")
            raise PredictionError(f"Error in URL preprocessing: {str(e)}")

    def _calculate_feature_contributions(self, features: pd.DataFrame, importance_dict: dict) -> Dict[str, float]:
        """Calculate feature contributions to the prediction."""
        contributions = {}
        for feature in self.feature_columns:
            value = features[feature].iloc[0]
            importance = importance_dict.get(feature, 0)
            contributions[feature] = float(value * importance)
        return contributions

    def predict(self, url: str) -> dict:
        try:
            processed_data = self.preprocess_url(url)
            prediction = self.model.predict(processed_data)[0]
            prediction_proba = self.model.predict_proba(processed_data)[0]
            
            result = "BEWARE MALICIOUS WEBSITE" if prediction == 1 else "SAFE WEBSITE"
            confidence = float(prediction_proba[1] if prediction == 1 else prediction_proba[0])
            
            # Get feature importance
            feature_importance = (
                dict(zip(self.feature_columns, self.model.feature_importances_))
                if hasattr(self.model, 'feature_importances_')
                else {col: 1.0/len(self.feature_columns) for col in self.feature_columns}
            )
            
            # Calculate feature contributions
            feature_contributions = self._calculate_feature_contributions(
                processed_data, feature_importance
            )
            
            # Get top indicators
            top_indicators = sorted(
                feature_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]
            
            return {
                "url": url,
                "result": result,
                "confidence": confidence,
                "feature_contributions": feature_contributions,
                "top_indicators": top_indicators
            }
            
        except Exception as e:
            logger.error(f"Error in URL prediction: {str(e)}")
            raise PredictionError(f"Error in URL prediction: {str(e)}")