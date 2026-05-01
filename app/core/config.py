from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lawgic MVP API"
    app_version: str = "0.2.0"

    chroma_collection: str = "lawgic_contract_clauses"
    chroma_persist_dir: str = "./data/chroma"

    llm_provider: str = "mock"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
