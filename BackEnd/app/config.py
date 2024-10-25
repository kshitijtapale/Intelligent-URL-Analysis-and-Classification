from pydantic_settings import BaseSettings
import os
from typing import ClassVar  

class Settings(BaseSettings):
    APP_NAME: str = "Malicious URL Detector"
    DATA_DIR: str = "artifacts"
    READY_MODEL_DIR: str = "artifacts/models/ready"
    PREPROCESSOR_MODEL_DIR: str = "artifacts/models/preprocessor"
    RAW_DATASET: str = "artifacts/raw_dataset"
    EXTRACTED_DATA: str = "artifacts/extracted_data"
    RAW_DATA_DIR: str = "artifacts/data_ingestion/raw_data"
    TEST_DATA_DIR: str = "artifacts/data_ingestion/test_data"
    TRAIN_DATA_DIR: str = "artifacts/data_ingestion/train_data"
    LOG_DIR: str = "logs"
    MODEL_FILENAME: str = "Best_Model.pkl"
    PREPROCESSOR_FILENAME: str = "preprocessor.pkl"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DB_HOST: str = "localhost"
    DB_USER: str = "root"  # Replace with your MySQL username
    DB_PASSWORD: str = "root"  # Replace with your MySQL password
    DB_NAME: str = "url"
    DATABASE_URL: str = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    



    class Config:
        env_file = ".env"

settings = Settings()

# List of directories to ensure exist
directories = [
    settings.DATA_DIR,
    settings.READY_MODEL_DIR,
    settings.PREPROCESSOR_MODEL_DIR,
    settings.RAW_DATASET,
    settings.EXTRACTED_DATA,
    settings.RAW_DATA_DIR,
    settings.TEST_DATA_DIR,
    settings.TRAIN_DATA_DIR,
    settings.LOG_DIR
]

# Ensure each directory exists
for directory in directories:
    os.makedirs(directory, exist_ok=True)
