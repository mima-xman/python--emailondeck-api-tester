import os
from pymongo import MongoClient
from dotenv import load_dotenv
from utils import logger, format_error

# Load environment variables
load_dotenv()


class DatabaseManager:
    _instance = None
    _client = None
    _db = None

    def __new__(cls, level: int = 0):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize(level=level)
        return cls._instance

    def _initialize(self, level: int = 0):
        """
        Initialize the MongoDB connection safely.
        """
        mongodb_uri = (
            os.getenv('BYTEZ_KEYS_MONGODB_URI') or 
            os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        )
        db_name = os.getenv('BYTEZ_KEYS_DB_NAME', 'bytez_keys_manager')

        try:
            self._client = MongoClient(mongodb_uri)
            self._db = self._client[db_name]
            # Verify connection
            # self._client.admin.command('ping')
            logger(f"Mongodb URI: {mongodb_uri[:20]}...", level=level)
            logger(f"✅ DatabaseManager connected to {db_name}", level=level)
        except Exception as e:
            logger(f"❌ DatabaseManager Logic Error: {format_error(e)}", level=level)
            self._client = None
            self._db = None

    @property
    def db(self, level: int = 0):
        """Returns the database object."""
        if self._db is None:
            # Try to re-initialize if connection failed previously
            self._initialize(level=level)
        return self._db

    def get_collection(self, collection_name):
        """Returns a specific collection safely."""
        if self.db is not None:
            return self.db[collection_name]
        return None
