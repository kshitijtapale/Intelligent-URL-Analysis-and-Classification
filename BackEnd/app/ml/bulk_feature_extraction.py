import pandas as pd
from app.ml.feature_extraction import FeatureExtractor
from app.logger import setup_logger
from app.exceptions import FeatureExtractionError
from typing import List, Dict, Optional
import os
import glob
from fastapi import UploadFile
from app.config import settings
import chardet

logger = setup_logger(__name__)

class BulkFeatureExtractor:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.raw_dataset_dir = settings.RAW_DATASET
        self.extracted_data_dir = settings.EXTRACTED_DATA

    async def extract_features_from_csv(self, check_google_index: bool = False, uploaded_file: Optional[UploadFile] = None) -> str:
        try:
            os.makedirs(self.raw_dataset_dir, exist_ok=True)
            os.makedirs(self.extracted_data_dir, exist_ok=True)

            if uploaded_file:
                input_file = os.path.join(self.raw_dataset_dir, uploaded_file.filename)
                content = await uploaded_file.read()
                with open(input_file, "wb") as buffer:
                    buffer.write(content)
                logger.info(f"Uploaded file saved as: {input_file}")
            else:
                csv_files = glob.glob(os.path.join(self.raw_dataset_dir, "*.csv"))
                if not csv_files:
                    raise FileNotFoundError(f"No CSV files found in {self.raw_dataset_dir}")
                input_file = max(csv_files, key=os.path.getctime)

            logger.info(f"Processing file: {input_file}")

            # Try to open CSV with default utf-8 encoding, if it fails, fall back to other encodings
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 encoding failed for {input_file}, attempting to auto-detect encoding.")
                
                with open(input_file, 'rb') as rawdata:
                    result = chardet.detect(rawdata.read())
                    detected_encoding = result['encoding']
                    logger.info(f"Detected encoding: {detected_encoding}")

                try:
                    df = pd.read_csv(input_file, encoding=detected_encoding)
                except Exception:
                    logger.warning(f"Detected encoding {detected_encoding} failed, falling back to ISO-8859-1")
                    df = pd.read_csv(input_file, encoding='ISO-8859-1')

            # Ensure 'url' and 'type' columns are present
            if 'url' not in df.columns or 'type' not in df.columns:
                raise ValueError("Input CSV must contain 'url' and 'type' columns")

            # Map 'type' to numeric label
            df['label'] = df['type'].map({'benign': 0, 'malicious': 1})

            features: List[Dict] = []
            for _, row in df.iterrows():
                feature_dict = self.feature_extractor.extract_features(row['url'], row['label'])
                features.append(feature_dict)

            features_df = pd.DataFrame(features)

            # Combine original dataframe with extracted features
            result_df = pd.concat([df[['url', 'label']], features_df], axis=1)

            # Rename columns to match expected output
            column_mapping = {
                'count_dot': 'count.',
                'count_www': 'count-www',
                'count_atrate': 'count@',
                'count_percentage': 'count%',
                'count_ques': 'count?',
                'count_hyphen': 'count-',
                'count_equal': 'count='
            }
            result_df = result_df.rename(columns=column_mapping)

            # Reorder columns to match the desired output
            desired_order = ['url', 'label', 'result', 'use_of_ip', 'abnormal_url', 'count.', 'count-www', 
                             'count@', 'count_dir', 'count_embed_domain', 'sus_url', 'short_url', 'count_https', 
                             'count_http', 'count%', 'count?', 'count-', 'count=', 'url_length', 
                             'hostname_length', 'fd_length', 'tld', 'tld_length', 'count_digits', 'count_letters']

            result_df = result_df.reindex(columns=desired_order)

            input_filename = os.path.basename(input_file)
            output_filename = f"preprocessed_{input_filename}"
            output_file = os.path.join(self.extracted_data_dir, output_filename)

            result_df.to_csv(output_file, index=False)
            logger.info(f"Feature extraction completed. Results saved to {output_file}")

            return output_file

        except Exception as e:
            logger.error(f"Error in bulk feature extraction: {str(e)}")
            raise FeatureExtractionError(f"Bulk feature extraction failed: {str(e)}")