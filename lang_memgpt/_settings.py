from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""
    pinecone_namespace: str = "ns1"
    model: str = "accounts/fireworks/models/firefunction-v2"


SETTINGS = Settings()
