from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    gmail_credentials_path: str
    mcp_host: str = "http://localhost:9000"
    model_name: str = "gpt-4.1-mini"

settings = Settings()