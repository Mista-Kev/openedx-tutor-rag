"""
Configuration for MongoDB and Qdrant connections.

These defaults work inside the Tutor Docker network where services
are available by their container names (mongodb, qdrant).
For local development outside Docker, override with environment variables.
"""

import os


class MongoConfig:
    """MongoDB connection settings from Tutor's defaults."""

    def __init__(self):
        self.host = os.getenv("MONGO_HOST", "mongodb")
        self.port = int(os.getenv("MONGO_PORT", 27017))
        self.database = os.getenv("MONGO_DB_NAME", "openedx")
        self.connection_string = f"mongodb://{self.host}:{self.port}"


class QdrantConfig:
    """Qdrant vector database settings."""

    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.collection_name = "openedx_courses"
        self.url = f"http://{self.host}:{self.port}"


# ready to import
mongo_config = MongoConfig()
qdrant_config = QdrantConfig()
