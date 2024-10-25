import os
from app.models.url_feedback import URLFeedback, get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import hashlib
from urllib.parse import urlparse
from typing import Dict, Optional
from app.logger import setup_logger
from app.ml.model_trainer import ModelTrainer
from app.ml.feature_extraction import FeatureExtractor
from app.ml.data_ingestion_transformation import DataIngestionTransformation
from app.config import settings
import pandas as pd

logger = setup_logger(__name__)

class AdaptiveLearner:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.model_trainer = ModelTrainer()
        self.data_ingestion = DataIngestionTransformation()
        self.retrain_threshold = 1000
        self.confidence_threshold = 0.8

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to handle duplicates with slight variations."""
        try:
            parsed = urlparse(url.lower())
            normalized = f"{parsed.netloc}{parsed.path}"
            normalized = normalized.rstrip('/')
            normalized = normalized.replace('www.', '')
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing URL {url}: {str(e)}")
            return url

    def _generate_url_hash(self, normalized_url: str) -> str:
        """Generate hash for normalized URL."""
        return hashlib.md5(normalized_url.encode()).hexdigest()

    def _resolve_conflicting_feedback(self, existing_record: URLFeedback, new_feedback: bool, new_confidence: float) -> Optional[Dict]:
        """Resolve conflicts in feedback using confidence and history."""
        try:
            existing_type = existing_record.type == 'malicious'
            
            if existing_record.consensus_reached:
                if new_confidence > max(0.95, existing_record.confidence):
                    return {
                        'type': 'malicious' if new_feedback else 'benign',
                        'confidence': new_confidence,
                        'feedback_count': existing_record.feedback_count + 1,
                        'conflicting_feedbacks': existing_record.conflicting_feedbacks + 1,
                        'last_feedback_type': 'malicious' if new_feedback else 'benign',
                        'consensus_reached': False
                    }
                return None

            if existing_type != new_feedback:
                if new_confidence > existing_record.confidence + 0.1:
                    return {
                        'type': 'malicious' if new_feedback else 'benign',
                        'confidence': new_confidence,
                        'feedback_count': existing_record.feedback_count + 1,
                        'conflicting_feedbacks': existing_record.conflicting_feedbacks + 1,
                        'last_feedback_type': 'malicious' if new_feedback else 'benign',
                        'consensus_reached': False
                    }
                previous_feedbacks = existing_record.last_feedback_type.split(',')
                same_feedback_count = sum(1 for t in previous_feedbacks 
                                        if t == ('malicious' if new_feedback else 'benign'))
                if same_feedback_count >= len(previous_feedbacks) / 2:
                    return {
                        'type': 'malicious' if new_feedback else 'benign',
                        'confidence': max(existing_record.confidence, new_confidence),
                        'feedback_count': existing_record.feedback_count + 1,
                        'conflicting_feedbacks': existing_record.conflicting_feedbacks + 1,
                        'last_feedback_type': f"{existing_record.last_feedback_type},{'malicious' if new_feedback else 'benign'}",
                        'consensus_reached': True
                    }
            else:
                return {
                    'type': 'malicious' if new_feedback else 'benign',
                    'confidence': max(existing_record.confidence, new_confidence),
                    'feedback_count': existing_record.feedback_count + 1,
                    'conflicting_feedbacks': existing_record.conflicting_feedbacks,
                    'last_feedback_type': f"{existing_record.last_feedback_type},{'malicious' if new_feedback else 'benign'}",
                    'consensus_reached': True if existing_record.feedback_count >= 2 else False
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in _resolve_conflicting_feedback: {str(e)}")
            raise Exception(f"Error resolving feedback conflict: {str(e)}")

    async def process_feedback(self, url: str, is_malicious: bool, confidence: float, db: Session) -> Dict:
        """Process new feedback data with proper update handling."""
        try:
            # Normalize URL and generate hash
            normalized_url = self._normalize_url(url)
            url_hash = self._generate_url_hash(normalized_url)
            current_time = datetime.utcnow()

            # Check for existing feedback
            existing_record = db.query(URLFeedback).filter(URLFeedback.url_hash == url_hash).first()
            
            if existing_record:
                logger.info(f"Found existing record for URL: {url}")
                logger.info(f"Current type: {existing_record.type}, New type: {'malicious' if is_malicious else 'benign'}")
                
                # Update feedback count and handle type change
                new_feedback_count = existing_record.feedback_count + 1
                
                # Check if type is changing
                is_type_change = (existing_record.type == 'malicious') != is_malicious
                new_conflicting_feedbacks = (
                    existing_record.conflicting_feedbacks + 1 if is_type_change 
                    else existing_record.conflicting_feedbacks
                )
                
                # Update the record with new values
                updates = {
                    'type': 'malicious' if is_malicious else 'benign',
                    'confidence': max(confidence, existing_record.confidence) if not is_type_change else confidence,
                    'feedback_count': new_feedback_count,
                    'conflicting_feedbacks': new_conflicting_feedbacks,
                    'last_feedback_type': (f"{existing_record.last_feedback_type},"
                                        f"{'malicious' if is_malicious else 'benign'}"),
                    'timestamp': current_time,
                    'used_in_training': False  # Reset training flag on update
                }
                
                # Determine consensus based on feedback history
                feedback_history = updates['last_feedback_type'].split(',')
                malicious_count = sum(1 for f in feedback_history if f == 'malicious')
                benign_count = len(feedback_history) - malicious_count
                
                # Set consensus based on majority and minimum feedback count
                if new_feedback_count >= 2:
                    majority_threshold = new_feedback_count * 0.6  # 60% majority
                    updates['consensus_reached'] = (
                        malicious_count >= majority_threshold or 
                        benign_count >= majority_threshold
                    )
                    updates['type'] = (
                        'malicious' if malicious_count >= benign_count 
                        else 'benign'
                    )
                
                # Log the update details
                logger.info(f"Updating record with values: {updates}")
                
                # Update the record
                for key, value in updates.items():
                    setattr(existing_record, key, value)
                
                db.commit()
                db.refresh(existing_record)
                
                logger.info(f"Updated record - Type: {existing_record.type}, "
                        f"Feedback Count: {existing_record.feedback_count}, "
                        f"Consensus: {existing_record.consensus_reached}")
                
                update_status = "updated"
                current_record = existing_record
                
            else:
                # Create new record
                new_record = URLFeedback(
                    url=url,
                    url_hash=url_hash,
                    normalized_url=normalized_url,
                    type='malicious' if is_malicious else 'benign',
                    confidence=confidence,
                    last_feedback_type='malicious' if is_malicious else 'benign',
                    timestamp=current_time,
                    feedback_count=1,
                    conflicting_feedbacks=0,
                    consensus_reached=False,
                    used_in_training=False
                )
                
                db.add(new_record)
                db.commit()
                db.refresh(new_record)
                
                logger.info(f"Created new record for URL: {url}")
                update_status = "new"
                current_record = new_record

            # Verify the record after update
            verified_record = db.query(URLFeedback).filter(URLFeedback.url_hash == url_hash).first()
            logger.info(f"Verified record state - Type: {verified_record.type}, "
                    f"Feedback Count: {verified_record.feedback_count}")

            # Check if retraining is needed
            unused_samples = db.query(URLFeedback).filter(
                URLFeedback.used_in_training == False,
                (URLFeedback.consensus_reached == True) | 
                (URLFeedback.feedback_count >= 2)
            ).count()
            
            needs_retraining = unused_samples >= self.retrain_threshold
            
            return {
                "message": f"Feedback {update_status} successfully",
                "needs_retraining": needs_retraining,
                "unused_samples": unused_samples,
                "feedback_status": update_status,
                "current_values": {
                    "url": verified_record.url,
                    "type": verified_record.type,
                    "confidence": float(verified_record.confidence),
                    "feedback_count": verified_record.feedback_count,
                    "conflicting_feedbacks": verified_record.conflicting_feedbacks,
                    "consensus_reached": verified_record.consensus_reached,
                    "last_feedback_type": verified_record.last_feedback_type,
                    "last_update": verified_record.timestamp.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            db.rollback()
            raise Exception(f"Error processing feedback: {str(e)}")
        

    async def retrain_model(self, db: Session) -> Dict:
        """Retrain model using database records."""
        try:
            # Get all records ready for training
            training_records = db.query(URLFeedback).filter(
                URLFeedback.used_in_training == False,
                (URLFeedback.consensus_reached == True) | (URLFeedback.feedback_count >= 2)
            ).all()

            logger.info(f"Found {len(training_records)} records for training")

            if len(training_records) < self.retrain_threshold:
                return {
                    "message": "Not enough new data for retraining",
                    "unused_samples": len(training_records),
                    "threshold": self.retrain_threshold
                }

            logger.info(f"Starting retraining with {len(training_records)} new samples")

            # Extract features from new URLs
            new_features = []
            processed_urls = 0
            failed_urls = 0

            for record in training_records:
                try:
                    features = self.feature_extractor.extract_features(record.url)
                    features['url'] = record.url
                    features['type'] = record.type
                    new_features.append(features)
                    processed_urls += 1
                    
                    if processed_urls % 100 == 0:  # Log progress every 100 URLs
                        logger.info(f"Processed {processed_urls}/{len(training_records)} URLs")
                        
                except Exception as e:
                    failed_urls += 1
                    logger.error(f"Error extracting features for URL {record.url}: {str(e)}")
                    continue

            if not new_features:
                raise Exception("No valid features extracted from feedback data")

            logger.info(f"Successfully processed {processed_urls} URLs, {failed_urls} failed")

            # Create DataFrame from new features
            new_data_df = pd.DataFrame(new_features)
            
            # Load existing training data
            try:
                existing_data = pd.read_csv(os.path.join(settings.TRAIN_DATA_DIR, "transformed_train_data.csv"))
                logger.info(f"Loaded existing training data: {len(existing_data)} records")
            except FileNotFoundError:
                logger.warning("No existing training data found, using only new data")
                existing_data = pd.DataFrame()

            # Combine data if existing data is available
            if not existing_data.empty:
                combined_data = pd.concat([existing_data, new_data_df], ignore_index=True)
                logger.info(f"Combined data size: {len(combined_data)} records")
            else:
                combined_data = new_data_df
                logger.info(f"Using only new data: {len(combined_data)} records")

            # Save combined data
            os.makedirs(settings.EXTRACTED_DATA, exist_ok=True)
            combined_file_path = os.path.join(settings.EXTRACTED_DATA, "combined_training_data.csv")
            combined_data.to_csv(combined_file_path, index=False)
            logger.info(f"Saved combined data to {combined_file_path}")

            # Perform data ingestion and transformation
            train_df, test_df, preprocessor_file = await self.data_ingestion.initiate_data_ingestion_transformation(
                custom_file_path=combined_file_path
            )

            # Train new model
            X_train = train_df.drop('label', axis=1)
            y_train = train_df['label']
            X_test = test_df.drop('label', axis=1)
            y_test = test_df['label']

            training_results = self.model_trainer.initiate_model_training(
                X_train, y_train, X_test, y_test
            )

            # Mark records as used in training
            for record in training_records:
                record.used_in_training = True
            db.commit()

            logger.info("Successfully marked records as used in training")

            # Clean up temporary files
            try:
                os.remove(combined_file_path)
                logger.info("Cleaned up temporary training files")
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {e}")

            return {
                "message": "Model retrained successfully",
                "new_samples_used": processed_urls,
                "failed_samples": failed_urls,
                "training_results": {
                    "model_name": training_results.get("best_model", "Unknown"),
                    "accuracy": training_results.get("model_performance", {}).get("accuracy", 0),
                    "precision": training_results.get("model_performance", {}).get("precision", 0),
                    "recall": training_results.get("model_performance", {}).get("recall", 0),
                    "f1_score": training_results.get("model_performance", {}).get("f1_score", 0)
                },
                "data_stats": {
                    "total_records": len(combined_data),
                    "new_records": len(new_features),
                    "existing_records": len(existing_data) if not existing_data.empty else 0
                }
            }

        except Exception as e:
            logger.error(f"Error in model retraining: {str(e)}")
            logger.exception("Detailed error trace:")
            db.rollback()  # Rollback any pending database changes
            raise Exception(f"Error in model retraining: {str(e)}")


    async def get_training_stats(self, db: Session) -> Dict:
        """Get statistics about training data and feedback."""
        try:
            # Get total records
            total_records = db.query(URLFeedback).count()
            
            # Get unused records eligible for training
            unused_records = db.query(URLFeedback).filter(
                URLFeedback.used_in_training == False,
                (URLFeedback.consensus_reached == True) | (URLFeedback.feedback_count >= 2)
            ).count()

            # Get consensus statistics
            consensus_records = db.query(URLFeedback).filter(
                URLFeedback.consensus_reached == True
            ).count()

            # Get type distribution
            type_distribution = dict(db.query(
                URLFeedback.type,
                func.count(URLFeedback.id)
            ).group_by(URLFeedback.type).all())

            # Get feedback statistics
            avg_feedback_count = db.query(func.avg(URLFeedback.feedback_count)).scalar() or 0
            max_feedback_count = db.query(func.max(URLFeedback.feedback_count)).scalar() or 0

            return {
                "total_records": total_records,
                "unused_eligible_records": unused_records,
                "consensus_records": consensus_records,
                "type_distribution": type_distribution,
                "feedback_stats": {
                    "average_feedbacks": float(avg_feedback_count),
                    "max_feedbacks": int(max_feedback_count)
                },
                "needs_retraining": unused_records >= self.retrain_threshold,
                "remaining_until_retrain": max(0, self.retrain_threshold - unused_records)
            }

        except Exception as e:
            logger.error(f"Error getting training stats: {str(e)}")
            raise Exception(f"Error getting training stats: {str(e)}")
