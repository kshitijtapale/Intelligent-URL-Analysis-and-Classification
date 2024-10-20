import os
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
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

    def initiate_model_training(self, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        try:
            logger.info("Starting model training")

            # Define the Decision Tree model with the best parameters
            best_params = {'min_samples_split': 5, 'min_samples_leaf': 4, 'max_depth': 1000, 'criterion': 'entropy'}

            # Initialize and train the decision tree classifier
            model = DecisionTreeClassifier(**best_params)
            model.fit(X_train, y_train)

            # Make predictions
            y_pred = model.predict(X_test)

            # Evaluate the model
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')

            logger.info(f"Model performance: Accuracy={accuracy}, Precision={precision}, Recall={recall}, F1-score={f1}")
            logger.info("\n" + classification_report(y_test, y_pred))

            # Save the trained model
            os.makedirs(os.path.dirname(self.model_file_path), exist_ok=True)
            joblib.dump(model, self.model_file_path)
            logger.info(f"Model saved to {self.model_file_path}")

            return {
                "Model Name": "DecisionTreeClassifier",
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            }

        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            raise ModelTrainerError(f"Model training failed: {str(e)}")