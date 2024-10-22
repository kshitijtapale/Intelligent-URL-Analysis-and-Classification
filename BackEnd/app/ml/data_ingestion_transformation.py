import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
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
        self.scaler = StandardScaler()
        
        # Define fixed feature columns
        self.feature_columns = [
            'use_of_ip', 'abnormal_url', 'count.', 'count-www', 'count@', 
            'count_dir', 'count_embed_domain', 'sus_url', 'short_url', 
            'count_https', 'count_http', 'count%', 'count?', 'count-', 
            'count=', 'url_length', 'hostname_length', 'fd_length', 
            'tld_length', 'count_digits', 'count_letters', 'has_valid_dns', 
            'has_dns_record', 'domain_length', 'has_https', 'domain_in_path', 
            'path_length', 'qty_params', 'qty_fragments', 'qty_special_chars', 
            'param_length', 'fragment_length', 'domain_token_count', 
            'qty_sensitive_words', 'has_client', 'has_admin', 'has_server', 
            'has_login', 'has_signup', 'has_password', 'has_security', 
            'has_verify', 'has_auth', 'subdomain_length', 'qty_subdomains', 
            'domain_hyphens', 'domain_underscores', 'domain_digits', 'has_port', 
            'is_ip', 'qty_mx_records', 'qty_txt_records', 'qty_ns_records'
        ]

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

    def _preprocess_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess features and handle missing values."""
        df = df.copy()
        
        # Handle missing values in numeric columns
        for col in self.feature_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        return df

    def initiate_data_ingestion_transformation(self, custom_file_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        logger.info("Initiating data ingestion and transformation process.")
        try:
            # Use custom file path if provided, otherwise use the latest preprocessed file
            if custom_file_path:
                if not os.path.exists(custom_file_path):
                    raise FileNotFoundError(f"Custom file not found: {custom_file_path}")
                input_file = custom_file_path
            else:
                input_file = self._get_latest_preprocessed_file()
            
            logger.info(f"Processing file: {input_file}")

            # Read the dataset
            df = pd.read_csv(input_file)
            logger.info(f"Initial dataset shape: {df.shape}")

            # Preprocess features
            df = self._preprocess_features(df)

            # Split features and target
            X = df[self.feature_columns]
            y = df['label']

            # Split the dataset
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Scale the features
            X_train_scaled = pd.DataFrame(
                self.scaler.fit_transform(X_train),
                columns=X_train.columns
            )
            X_test_scaled = pd.DataFrame(
                self.scaler.transform(X_test),
                columns=X_test.columns
            )

            # Combine scaled features with target
            train_df = pd.concat([X_train_scaled, y_train.reset_index(drop=True)], axis=1)
            test_df = pd.concat([X_test_scaled, y_test.reset_index(drop=True)], axis=1)

            # Save transformed data
            train_df.to_csv(self.train_data_path, index=False)
            test_df.to_csv(self.test_data_path, index=False)

            # Save preprocessor components
            preprocessor_dict = {
                "scaler": self.scaler,
                "feature_columns": self.feature_columns
            }

            with open(self.preprocessor_file_path, 'wb') as f:
                pickle.dump(preprocessor_dict, f)

            logger.info(f"Saved preprocessor file at: {self.preprocessor_file_path}")

            return train_df, test_df, self.preprocessor_file_path

        except Exception as e:
            logger.error(f"Exception occurred in data ingestion and transformation: {str(e)}")
            raise DataIngestionError(f"Error in data ingestion and transformation: {str(e)}")

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