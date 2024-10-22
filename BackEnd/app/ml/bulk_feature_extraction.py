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
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import multiprocessing
from itertools import islice
import numpy as np

logger = setup_logger(__name__)

class BulkFeatureExtractor:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.raw_dataset_dir = settings.RAW_DATASET
        self.extracted_data_dir = settings.EXTRACTED_DATA
        # Calculate optimal chunk size based on system resources
        self.chunk_size = 1000  # Process 1000 URLs at a time
        self.n_workers = min(multiprocessing.cpu_count(), 8)  # Use up to 8 CPU cores

    async def extract_features_from_csv(self, check_google_index: bool = False, uploaded_file: Optional[UploadFile] = None) -> str:
        try:
            os.makedirs(self.raw_dataset_dir, exist_ok=True)
            os.makedirs(self.extracted_data_dir, exist_ok=True)

            # Handle file input
            input_file = await self._handle_input_file(uploaded_file)
            logger.info(f"Processing file: {input_file}")

            # Read the dataset efficiently
            df = self._read_csv_efficiently(input_file)
            total_urls = len(df)
            logger.info(f"Total URLs to process: {total_urls}")

            # Process URLs in chunks
            processed_features = self._process_urls_in_parallel(df)

            # Create final dataframe
            features_df = pd.DataFrame(processed_features)
            
            # Combine with original URLs and labels
            result_df = pd.concat([
                df[['url', 'type']],  # Keep original URL and type columns
                features_df
            ], axis=1)

            # Map type to numeric label
            result_df['label'] = result_df['type'].map({'benign': 0, 'malicious': 1})

            # Ensure all required columns are present
            result_df = self._ensure_all_columns(result_df)

            # Save the processed dataset
            output_file = self._save_processed_dataset(input_file, result_df)
            
            logger.info(f"Feature extraction completed. Results saved to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error in bulk feature extraction: {str(e)}")
            raise FeatureExtractionError(f"Bulk feature extraction failed: {str(e)}")

    async def _handle_input_file(self, uploaded_file: Optional[UploadFile]) -> str:
        """Handle file upload or use existing file."""
        if uploaded_file:
            input_file = os.path.join(self.raw_dataset_dir, uploaded_file.filename)
            content = await uploaded_file.read()
            with open(input_file, "wb") as buffer:
                buffer.write(content)
            return input_file
        else:
            csv_files = glob.glob(os.path.join(self.raw_dataset_dir, "*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {self.raw_dataset_dir}")
            return max(csv_files, key=os.path.getctime)

    def _read_csv_efficiently(self, file_path: str) -> pd.DataFrame:
        """Read CSV file with robust encoding detection and handling."""
        encodings_to_try = [
            'utf-8', 
            'utf-8-sig',  # UTF-8 with BOM
            'latin1',     # Also known as ISO-8859-1
            'iso-8859-1',
            'cp1252',     # Windows-1252
            'ascii'
        ]
        
        # First try chardet for automatic detection
        try:
            with open(file_path, 'rb') as rawdata:
                # Read a larger chunk for better encoding detection
                chunk = rawdata.read(min(32768, os.path.getsize(file_path)))
                detected = chardet.detect(chunk)
                if detected['confidence'] > 0.7:  # Only use if confidence is high enough
                    try:
                        df = pd.read_csv(file_path, encoding=detected['encoding'])
                        logger.info(f"Successfully read CSV with detected encoding: {detected['encoding']}")
                        if {'url', 'type'}.issubset(df.columns):
                            return df
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"Chardet detection failed: {str(e)}")

        # Try each encoding in our list
        last_exception = None
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read CSV with encoding: {encoding}")
                if {'url', 'type'}.issubset(df.columns):
                    return df
            except Exception as e:
                last_exception = e
                continue

        # If all attempts fail, try reading with error handling
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            if {'url', 'type'}.issubset(df.columns):
                logger.warning("CSV read with skipped bad lines")
                return df
        except Exception as e:
            last_exception = e

        # If everything fails, raise the last exception
        logger.error(f"Failed to read CSV with any encoding: {str(last_exception)}")
        raise last_exception

    def _process_chunk(self, urls: List[str]) -> List[Dict]:
        """Process a chunk of URLs."""
        features = []
        for url in urls:
            try:
                # Extract features without WHOIS lookup
                feature_dict = self.feature_extractor.extract_features(url)
                features.append(feature_dict)
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                features.append(self._get_default_features())
        return features

    def _process_urls_in_parallel(self, df: pd.DataFrame) -> List[Dict]:
        """Process URLs in parallel using chunks."""
        all_features = []
        total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size
        
        with tqdm(total=len(df), desc="Extracting features") as pbar:
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                # Process chunks in parallel
                futures = []
                for i in range(0, len(df), self.chunk_size):
                    chunk = df['url'].iloc[i:i + self.chunk_size].tolist()
                    futures.append(executor.submit(self._process_chunk, chunk))

                # Collect results
                for future in as_completed(futures):
                    chunk_features = future.result()
                    all_features.extend(chunk_features)
                    pbar.update(len(chunk_features))

        return all_features

    def _get_default_features(self) -> Dict:
        """Return default feature values for failed extractions."""
        return {
            # Lexical features
            'use_of_ip': 0,
            'abnormal_url': 0,
            'count.': 0,
            'count-www': 0,
            'count@': 0,
            'count_dir': 0,
            'count_embed_domain': 0,
            'sus_url': 0,
            'short_url': 0,
            'count_https': 0,
            'count_http': 0,
            'count%': 0,
            'count?': 0,
            'count-': 0,
            'count=': 0,
            'url_length': 0,
            'hostname_length': 0,
            'fd_length': 0,
            'tld': '',
            'tld_length': 0,
            'count_digits': 0,
            'count_letters': 0,
            
            # Host-based features
            'has_valid_dns': 0,
            'has_dns_record': 0,
            'domain_length': 0,
            'has_https': 0,
            'domain_in_path': 0,
            'path_length': 0,
            'qty_params': 0,
            'qty_fragments': 0,
            'qty_special_chars': 0,
            'param_length': 0,
            'fragment_length': 0,
            'domain_token_count': 0,
            
            # Security features
            'qty_sensitive_words': 0,
            'has_client': 0,
            'has_admin': 0,
            'has_server': 0,
            'has_login': 0,
            'has_signup': 0,
            'has_password': 0,
            'has_security': 0,
            'has_verify': 0,
            'has_auth': 0,
            
            # Domain features
            'subdomain_length': 0,
            'qty_subdomains': 0,
            'domain_hyphens': 0,
            'domain_underscores': 0,
            'domain_digits': 0,
            'has_port': 0,
            'is_ip': 0,
            
            # DNS features
            'qty_mx_records': 0,
            'qty_txt_records': 0,
            'qty_ns_records': 0
        }

    def _ensure_all_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns are present with correct names."""
        required_columns = [
            'url', 'type', 'label',
            # Lexical features
            'use_of_ip', 'abnormal_url', 'count.', 'count-www', 'count@',
            'count_dir', 'count_embed_domain', 'sus_url', 'short_url',
            'count_https', 'count_http', 'count%', 'count?', 'count-',
            'count=', 'url_length', 'hostname_length', 'fd_length',
            'tld', 'tld_length', 'count_digits', 'count_letters',
            
            # Host-based features
            'has_valid_dns', 'has_dns_record', 'domain_length', 'has_https',
            'domain_in_path', 'path_length', 'qty_params', 'qty_fragments',
            'qty_special_chars', 'param_length', 'fragment_length',
            'domain_token_count',
            
            # Security features
            'qty_sensitive_words', 'has_client', 'has_admin', 'has_server',
            'has_login', 'has_signup', 'has_password', 'has_security',
            'has_verify', 'has_auth',
            
            # Domain features
            'subdomain_length', 'qty_subdomains', 'domain_hyphens',
            'domain_underscores', 'domain_digits', 'has_port', 'is_ip',
            
            # DNS features
            'qty_mx_records', 'qty_txt_records', 'qty_ns_records'
        ]
        
        # Add any missing columns with default values
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0 if col not in ['url', 'type', 'tld'] else ''

        # Ensure correct column order
        return df[required_columns]

    def _save_processed_dataset(self, input_file: str, df: pd.DataFrame) -> str:
        """Save the processed dataset."""
        input_filename = os.path.basename(input_file)
        output_filename = f"preprocessed_{input_filename}"
        output_file = os.path.join(self.extracted_data_dir, output_filename)
        
        # Save efficiently
        df.to_csv(output_file, index=False)
        return output_file