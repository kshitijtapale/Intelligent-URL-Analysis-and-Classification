import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from app.config import settings
from app.exceptions import ModelTrainerError
from typing import Dict, Any
import joblib
from app.logger import setup_logger

logger = setup_logger(__name__)

class ModelTrainer:
    def __init__(self):
        self.model_file_path = os.path.join(settings.READY_MODEL_DIR, settings.MODEL_FILENAME)
        self.models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        }

    def initiate_model_training(self, X_train: pd.DataFrame, y_train: pd.Series, 
                              X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """Train and evaluate model."""
        try:
            logger.info("Starting model training")
            
            if X_train.isna().any().any() or X_test.isna().any().any():
                raise ModelTrainerError("Input features contain NaN values")
            if y_train.isna().any() or y_test.isna().any():
                raise ModelTrainerError("Target variables contain NaN values")

            model_results = {}
            best_model = None
            best_model_name = None
            best_score = 0

            for model_name, model in self.models.items():
                logger.info(f"Training {model_name}")
                
                try:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    
                    metrics = {
                        'accuracy': float(accuracy_score(y_test, y_pred)),
                        'precision': float(precision_score(y_test, y_pred, average='weighted')),
                        'recall': float(recall_score(y_test, y_pred, average='weighted')),
                        'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
                    }
                    
                    logger.info(f"{model_name} metrics: {metrics}")
                    model_results[model_name] = metrics
                    
                    if metrics['f1_score'] > best_score:
                        best_score = metrics['f1_score']
                        best_model = model
                        best_model_name = model_name
                        
                except Exception as e:
                    logger.error(f"Error training {model_name}: {str(e)}")
                    continue
            
            if best_model is None:
                raise ModelTrainerError("No models were successfully trained")
            
            logger.info(f"Best performing model: {best_model_name}")
            
            # Save model and metadata
            os.makedirs(os.path.dirname(self.model_file_path), exist_ok=True)
            feature_columns = X_train.columns.tolist()
            
            model_data = {
                'model': best_model,
                'feature_columns': feature_columns,
                'feature_importance': dict(zip(
                    feature_columns,
                    best_model.feature_importances_
                )) if hasattr(best_model, 'feature_importances_') else None
            }
            
            joblib.dump(model_data, self.model_file_path)
            
            return {
                "message": "Model training completed successfully",
                "best_model": best_model_name,
                "model_performance": model_results[best_model_name],
                "selected_features": feature_columns,  # Added this field
                "best_model_file_path": self.model_file_path,
                "all_models_performance": model_results
            }
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            raise ModelTrainerError(f"Model training failed: {str(e)}")