import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from app.config import settings
from app.exceptions import DataIngestionError, DataTransformationError
from app.logger import setup_logger
import pickle
import glob
from typing import Tuple, Dict, Optional

logger = setup_logger(__name__)

class DataIngestionTransformation:
    def __init__(self):
        self.preprocessor_file_path = os.path.join(settings.PREPROCESSOR_MODEL_DIR, settings.PREPROCESSOR_FILENAME)
        self.train_data_path = os.path.join(settings.TRAIN_DATA_DIR, "transformed_train_data.csv")
        self.test_data_path = os.path.join(settings.TEST_DATA_DIR, "transformed_test_data.csv")

        # Ensure necessary directories exist
        os.makedirs(settings.TRAIN_DATA_DIR, exist_ok=True)
        os.makedirs(settings.TEST_DATA_DIR, exist_ok=True)
        os.makedirs(settings.PREPROCESSOR_MODEL_DIR, exist_ok=True)

    def _get_latest_preprocessed_file(self) -> str:
        """Find the latest preprocessed CSV file in the EXTRACTED_DATA directory."""
        extracted_files = glob.glob(os.path.join(settings.EXTRACTED_DATA, "preprocessed_*.csv"))
        if not extracted_files:
            raise FileNotFoundError(f"No preprocessed CSV files found in {settings.EXTRACTED_DATA}")
        return max(extracted_files, key=os.path.getctime)

    def initiate_data_ingestion_transformation(self, custom_file_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        logger.info("Initiating data ingestion and transformation process.")
        try:
            # Use custom file path if provided, otherwise use the latest preprocessed file.
            if custom_file_path:
                if not os.path.exists(custom_file_path):
                    raise FileNotFoundError(f"Custom file not found: {custom_file_path}")
                input_file = custom_file_path
                logger.info(f"Using custom file: {input_file}")
            else:
                input_file = self._get_latest_preprocessed_file()
                logger.info(f"Using latest preprocessed file: {input_file}")

            # Read the dataset into a pandas dataframe
            df = pd.read_csv(input_file)
            logger.info(f"Read dataset from {input_file}. Shape: {df.shape}")

            # Select features and target variable
            features = ['use_of_ip', 'abnormal_url', 'count.', 'count-www', 'count@',
                        'count_dir', 'count_embed_domain', 'short_url', 'count%', 'count?', 
                        'count-', 'count=', 'url_length', 'count_https', 'count_http', 
                        'hostname_length', 'sus_url', 'fd_length', 'tld_length', 'count_digits',
                        'count_letters']
            
            X = df[features]
            y = df['label']

            # Split the dataset into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

            logger.info("Train and test data split completed.")

            # Combine features and target for each set
            train_df = pd.concat([X_train, y_train], axis=1)
            test_df = pd.concat([X_test, y_test], axis=1)

            logger.info(f"Final train dataframe shape: {train_df.shape}")
            logger.info(f"Final test dataframe shape: {test_df.shape}")

            # Save transformed data
            train_df.to_csv(self.train_data_path, index=False)
            test_df.to_csv(self.test_data_path, index=False)

            logger.info(f"Saved transformed train data to {self.train_data_path}")
            logger.info(f"Saved transformed test data to {self.test_data_path}")

            # Save feature list
            preprocessor_dict = {
                "features": features
            }

            with open(self.preprocessor_file_path, 'wb') as f:
                pickle.dump(preprocessor_dict, f)

            logger.info(f"Saved preprocessor file at: {self.preprocessor_file_path}")

            return (
                train_df,
                test_df,
                self.preprocessor_file_path,
            )

        except Exception as e:
            logger.error(f"Exception occurred in the initiate_data_ingestion_transformation: {e}")
            raise DataIngestionError(f"Error occurred during data ingestion and transformation process: {str(e)}")

    @staticmethod
    def load_preprocessor(preprocessor_file_path: str) -> Dict:
        try:
            with open(preprocessor_file_path, 'rb') as f:
                preprocessor_dict = pickle.load(f)
            logger.info("Loaded preprocessor components successfully.")
            return preprocessor_dict
        except Exception as e:
            logger.error(f"Error loading preprocessor components: {e}")
            raise DataTransformationError(f"Error loading preprocessor components: {str(e)}")