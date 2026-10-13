import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Security & Auth
    JWT_SECRET_KEY: str = Field(default="change-this-in-production-buildtrust-secret-key-32chars-min")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480)

    INITIAL_ADMIN_EMAIL: str = Field(default="admin@buildtrust.ai")
    INITIAL_ADMIN_PASSWORD: str = Field(default="BuildTrustAdmin2026!")
    INITIAL_ADMIN_ROLE: str = Field(default="ADMIN")

    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")

    # Storage Backend: 'local' or 'aws'
    STORAGE_BACKEND: str = Field(default="local")
    LOCAL_STORAGE_DIR: str = Field(default="backend/data")

    # AWS
    AWS_REGION: str = Field(default="ap-south-1")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = Field(default="buildtrust-ai-evidence-vault-demo")
    DYNAMODB_TABLE_NAME: str = Field(default="BuildTrustRecords")
    CLOUDWATCH_LOG_GROUP: str = Field(default="/aws/apprunner/buildtrust-ai-backend")

    # OSV Vulnerability Scanner
    OSV_API_ENABLED: bool = Field(default=True)
    OSV_API_TIMEOUT_SECONDS: int = Field(default=10)
    OSV_BATCH_SIZE: int = Field(default=20)

    # ML
    ML_ENABLED: bool = Field(default=True)
    ML_MODEL_PATH: str = Field(default="backend/app/ml/models/isolation_forest.joblib")
    ML_CONTAMINATION_RATE: float = Field(default=0.08)

    # Ingestion limits
    MAX_EVIDENCE_PAYLOAD_BYTES: int = Field(default=10485760)
    MAX_ARTIFACT_UPLOAD_BYTES: int = Field(default=104857600)

    # Trust Engine Defaults
    POLICY_APPROVAL_THRESHOLD: float = Field(default=85.0)
    POLICY_REVIEW_THRESHOLD: float = Field(default=60.0)

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
