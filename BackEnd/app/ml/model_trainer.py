import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.model_selection import cross_val_score, RandomizedSearchCV, StratifiedKFold
from app.config import settings
from app.exceptions import ModelTrainerError
from typing import Dict, Any, Tuple
import joblib
from app.logger import setup_logger
from datetime import datetime
from tqdm import tqdm
from xgboost import XGBClassifier

logger = setup_logger(__name__)

class ModelTrainer:
    def __init__(self):
        self.best_model_file_path = os.path.join(settings.READY_MODEL_DIR, settings.MODEL_FILENAME)
        self.models_dir = os.path.join(settings.READY_MODEL_DIR, "all_models")
        os.makedirs(self.models_dir, exist_ok=True)
        
       
        self.param_grids = {
            'RandomForest': {
                'model': RandomForestClassifier(random_state=42, n_jobs=-1),
                'params': {
                    'n_estimators': [100],
                    'max_depth': [10, 15],
                    'min_samples_split': [5],
                    'min_samples_leaf': [2],
                    'class_weight': ['balanced']
                }
            },
            'GradientBoosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': [100],
                    'learning_rate': [0.1],
                    'max_depth': [3, 5],
                    'min_samples_split': [4],
                    'subsample': [0.8]
                }
            },
            'XGBoost': {
                'model': XGBClassifier(
                    random_state=42,
                    n_jobs=-1,
                    tree_method='hist'
                ),
                'params': {
                    'n_estimators': [100],
                    'max_depth': [3, 5],
                    'learning_rate': [0.1],
                    'subsample': [0.8],
                    'colsample_bytree': [0.8],
                    'scale_pos_weight': [3]
                }
            }
        }

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _save_model(self, model_name: str, model_data: Dict, metrics: Dict) -> str:
        timestamp = self._get_timestamp()
        filename = f"{model_name}_{timestamp}.pkl"
        filepath = os.path.join(self.models_dir, filename)
        
        save_data = {
            'model': model_data['model'],
            'feature_columns': model_data['feature_columns'],
            'feature_importance': model_data['feature_importance'],
            'best_params': model_data['best_params'],
            'metrics': metrics,
            'timestamp': timestamp
        }
        
        joblib.dump(save_data, filepath)
        logger.info(f"Saved {model_name} model to {filepath}")
        return filepath

    def _perform_cross_validation(self, model, X: pd.DataFrame, y: pd.Series, pbar: tqdm) -> Dict[str, float]:
        """Perform quick cross-validation with reduced folds."""
        try:
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            
            cv_scores = {
                'accuracy': cross_val_score(model, X, y, cv=cv, scoring='accuracy'),
                'precision': cross_val_score(model, X, y, cv=cv, scoring='precision_weighted'),
                'recall': cross_val_score(model, X, y, cv=cv, scoring='recall_weighted'),
                'f1': cross_val_score(model, X, y, cv=cv, scoring='f1_weighted')
            }
            
            return {
                'accuracy': float(cv_scores['accuracy'].mean()),
                'precision': float(cv_scores['precision'].mean()),
                'recall': float(cv_scores['recall'].mean()),
                'f1_score': float(cv_scores['f1'].mean()),
                'cv_std': {
                    'accuracy_std': float(cv_scores['accuracy'].std()),
                    'precision_std': float(cv_scores['precision'].std()),
                    'recall_std': float(cv_scores['recall'].std()),
                    'f1_std': float(cv_scores['f1'].std())
                }
            }
        except Exception as e:
            logger.error(f"Error in cross-validation: {str(e)}")
            raise ModelTrainerError(f"Cross-validation failed: {str(e)}")

    def _perform_randomized_search(self, model_name: str, X: pd.DataFrame, y: pd.Series, pbar: tqdm) -> Tuple[object, Dict]:
        """Perform randomized search with progress tracking."""
        try:
            model_info = self.param_grids[model_name]
            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            
            random_search = RandomizedSearchCV(
                estimator=model_info['model'],
                param_distributions=model_info['params'],
                n_iter=5,
                cv=cv,
                scoring='f1_weighted',
                n_jobs=-1,
                random_state=42,
                verbose=0
            )
            
            random_search.fit(X, y)
            logger.info(f"Best parameters for {model_name}: {random_search.best_params_}")
            
            return random_search.best_estimator_, random_search.best_params_
            
        except Exception as e:
            logger.error(f"Error in randomized search for {model_name}: {str(e)}")
            raise ModelTrainerError(f"Randomized search failed for {model_name}: {str(e)}")

    def initiate_model_training(self, X_train: pd.DataFrame, y_train: pd.Series, 
                              X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """Train and evaluate all models with progress tracking."""
        try:
            logger.info("Starting optimized model training process")
            
            if X_train.isna().any().any() or X_test.isna().any().any():
                raise ModelTrainerError("Input features contain NaN values")
            if y_train.isna().any() or y_test.isna().any():
                raise ModelTrainerError("Target variables contain NaN values")

            model_results = {}
            saved_model_paths = {}
            best_model = None
            best_model_name = None
            best_score = 0
            best_params = None

            # Calculate total steps
            total_steps = len(self.param_grids) * 3  # 3 steps per model
            
            # Create progress bar
            with tqdm(total=total_steps, desc="Training Progress") as pbar:
                # Train each model
                for model_name in self.param_grids.keys():
                    logger.info(f"Training {model_name}")
                    
                    try:
                        pbar.set_description(f"Parameter search - {model_name}")
                        tuned_model, best_params_model = self._perform_randomized_search(
                            model_name, X_train, y_train, pbar
                        )
                        pbar.update(1)

                        pbar.set_description(f"Cross-validation - {model_name}")
                        cv_metrics = self._perform_cross_validation(
                            tuned_model, X_train, y_train, pbar
                        )
                        pbar.update(1)

                        pbar.set_description(f"Final evaluation - {model_name}")
                        y_pred = tuned_model.predict(X_test)
                        test_metrics = {
                            'accuracy': float(accuracy_score(y_test, y_pred)),
                            'precision': float(precision_score(y_test, y_pred, average='weighted')),
                            'recall': float(recall_score(y_test, y_pred, average='weighted')),
                            'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
                        }
                        pbar.update(1)

                        logger.info(f"\nClassification Report for {model_name}:\n"
                                  f"{classification_report(y_test, y_pred)}")

                        # Save model data
                        model_data = {
                            'model': tuned_model,
                            'feature_columns': X_train.columns.tolist(),
                            'feature_importance': dict(zip(
                                X_train.columns,
                                tuned_model.feature_importances_
                            )) if hasattr(tuned_model, 'feature_importances_') else None,
                            'best_params': best_params_model
                        }

                        metrics = {
                            'cv_metrics': cv_metrics,
                            'test_metrics': test_metrics
                        }

                        model_path = self._save_model(model_name, model_data, metrics)
                        saved_model_paths[model_name] = model_path
                        
                        model_results[model_name] = {
                            'cv_metrics': cv_metrics,
                            'test_metrics': test_metrics,
                            'best_params': best_params_model,
                            'model_path': model_path
                        }
                        
                        if cv_metrics['f1_score'] > best_score:
                            best_score = cv_metrics['f1_score']
                            best_model = tuned_model
                            best_model_name = model_name
                            best_params = best_params_model
                            
                    except Exception as e:
                        logger.error(f"Error training {model_name}: {str(e)}")
                        pbar.update(3)  # Skip remaining steps for failed model
                        continue

            if best_model is None:
                raise ModelTrainerError("No models were successfully trained")
            
            logger.info(f"Best performing model: {best_model_name}")
            
            # Save best model
            best_model_data = {
                'model': best_model,
                'feature_columns': X_train.columns.tolist(),
                'feature_importance': dict(zip(
                    X_train.columns,
                    best_model.feature_importances_
                )) if hasattr(best_model, 'feature_importances_') else None,
                'best_params': best_params
            }
            
            joblib.dump(best_model_data, self.best_model_file_path)
            
            return {
                "message": "Model training completed successfully",
                "best_model": best_model_name,
                "model_performance": model_results[best_model_name]['test_metrics'],
                "cv_performance": model_results[best_model_name]['cv_metrics'],
                "selected_features": X_train.columns.tolist(),
                "best_model_file_path": self.best_model_file_path,
                "best_parameters": best_params,
                "all_models_paths": saved_model_paths,
                "all_models_performance": {
                    name: {
                        'test_metrics': results['test_metrics'],
                        'cv_metrics': results['cv_metrics'],
                        'best_params': results['best_params'],
                        'model_path': results['model_path']
                    }
                    for name, results in model_results.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            raise ModelTrainerError(f"Model training failed: {str(e)}")