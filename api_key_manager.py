from datetime import datetime, timezone, timedelta
import os
from bson import ObjectId
from db_manager import DatabaseManager
from utils import logger, format_error


class ApiKeyManager:
    """Manages API keys from MongoDB database"""
    
    def __init__(self, used_by=None, level: int = 0):
        """
        Initialize API Key Manager
        """
        self.used_by = used_by or os.getenv('USED_BY', 'emailondeck-api-tester')
        
        # Use centralized DB Manager
        self.db_manager = DatabaseManager(level=level)
        self.api_keys_collection = self.db_manager.get_collection('api_keys')
        self.usage_logs_collection = self.db_manager.get_collection('key_usage_logs')
        
        logger(f"✅ ApiKeyManager initialized: {self.used_by}", level=level)
    
    @staticmethod
    def sanitize_model_name(model_name):
        r"""
        Sanitize model name for use as MongoDB field key
        Replaces /, \, . with __
        
        Args:
            model_name: Original model name (e.g., "google/imagen-4.0-ultra-generate-001")
            
        Returns:
            Sanitized model name (e.g., "google__imagen-4__0-ultra-generate-001")
        """
        return model_name.replace('/', '__').replace('\\', '__').replace('.', '__')
    
    def acquire_key(self, model_name, generator_type="text", level: int = 0):
        """
        Acquire an available API key from database
        
        Args:
            model_name: Model name (e.g., "openai/gpt-5.1")
            generator_type: Type of generation ("text" or "image")
            
        Returns:
            Tuple of (api_key_id, api_key_string) or (None, None) if no keys available
        """
        try:
            sanitized_model = self.sanitize_model_name(model_name)
            expiration_field = f"models_expirations.{sanitized_model}"
            used_by_value = f"{self.used_by} - {generator_type}"
            
            # Query for available keys
            # Key must be: not in use AND (model not in expirations OR expired more than 24h ago)
            query = {
                "in_use": False,
                "$or": [
                    {expiration_field: {"$exists": False}},
                    {expiration_field: {"$lte": datetime.now(timezone.utc) - timedelta(days=30)}}
                ]
            }
            
            # Update to lock the key and remove expiration field if exists
            update = {
                "$set": {
                    "in_use": True,
                    "used_by": used_by_value,
                    "locked_at": datetime.now(timezone.utc),
                },
                "$unset": {
                    expiration_field: ""
                }
            }
            
            # Find and update atomically
            result = self.api_keys_collection.find_one_and_update(
                query,
                update,
                return_document=True  # Return the updated document
            )
            
            if result:
                api_key_id = str(result['_id'])
                api_key = result['api_key']
                logger(f"🔑 Acquired key: {api_key[:8]}... for {model_name} ({generator_type})", level=level)
                return api_key_id, api_key
            else:
                logger(f"❌ No available keys for {model_name} ({generator_type})", level=level)
                return None, None
                
        except Exception as e:
            logger(f"❌ Error acquiring key: {format_error(e)}", level=level)
            return None, None
    
    def release_key(self, api_key, level: int = 0):
        """
        Release a key back to the pool
        
        Args:
            api_key: The API key string to release
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update = {
                "$set": {
                    "in_use": False,
                    "used_by": None,
                    "locked_at": None
                }
            }
            
            result = self.api_keys_collection.update_one(
                {"api_key": api_key},
                update
            )
            
            if result.modified_count > 0:
                logger(f"🔓 Released key: {api_key[:8]}...", level=level)
                return True
            else:
                logger(f"⚠️ Key not found or already released: {api_key[:8]}...", level=level)
                return False
                
        except Exception as e:
            logger(f"❌ Error releasing key: {format_error(e)}", level=level)
            return False
    
    def log_usage(self, api_key_id, api_key, model_name, success, error=None, level: int = 0):
        """
        Log API key usage to database
        
        Args:
            api_key_id: The MongoDB ObjectId of the API key
            api_key: The API key string
            model_name: Model name used
            success: Whether the generation was successful
            error: Error message if failed (optional)
            
        Returns:
            Inserted log ID or None if failed
        """
        try:
            log_document = {
                "api_key_id": ObjectId(api_key_id),
                "api_key": api_key,
                "used_by": self.used_by,
                "used_at": datetime.now(timezone.utc),
                "model_name": model_name,
                "success": success,
                "error": error
            }
            
            result = self.usage_logs_collection.insert_one(log_document)
            
            status = "✅" if success else "❌"
            logger(f"{status} Logged usage: {model_name} - {api_key[:8]}... - Success: {success}", level=level)
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger(f"❌ Error logging usage: {format_error(e)}", level=level)
            return None
    
    def mark_key_expired_and_release(self, api_key, model_name, level: int = 0):
        """
        Atomically mark a key as expired for a specific model AND release it
        Single database operation for efficiency
        
        Args:
            api_key: The API key string
            model_name: Model name to mark as expired
            
        Returns:
            True if successful, False otherwise
        """
        try:
            sanitized_model = self.sanitize_model_name(model_name)
            expiration_field = f"models_expirations.{sanitized_model}"
            
            # Single atomic update: mark expired AND release
            update = {
                "$set": {
                    expiration_field: datetime.now(timezone.utc),
                    "in_use": False,
                    "used_by": None,
                    "locked_at": None
                }
            }
            
            result = self.api_keys_collection.update_one(
                {"api_key": api_key},
                update
            )
            
            if result.modified_count > 0:
                logger(f"⏰ Marked key as expired for {model_name} and released: {api_key[:8]}...", level=level)
                return True
            else:
                logger(f"⚠️ Key not found: {api_key[:8]}...", level=level)
                return False
                
        except Exception as e:
            logger(f"❌ Error marking key expired: {format_error(e)}", level=level)
            return False
    
    def release_all_keys(self, level: int = 0):
        """
        Release all keys currently locked by this generator
        Useful for cleanup on shutdown
        
        Returns:
            Number of keys released
        """
        try:
            # Find all keys used by this generator
            query = {
                "in_use": True,
                "used_by": {"$regex": f"^{self.generator_name}"}
            }
            
            update = {
                "$set": {
                    "in_use": False,
                    "used_by": None,
                    "locked_at": None
                }
            }
            
            result = self.api_keys_collection.update_many(query, update)
            
            if result.modified_count > 0:
                logger(f"🔓 Released {result.modified_count} keys on cleanup", level=level)
            
            return result.modified_count
            
        except Exception as e:
            logger(f"❌ Error releasing all keys: {format_error(e)}", level=level)
            return 0
    
    def __del__(self):
        """Cleanup: close MongoDB connection"""
        try:
            if hasattr(self, 'mongo_client'):
                self.mongo_client.close()
        except:
            pass
