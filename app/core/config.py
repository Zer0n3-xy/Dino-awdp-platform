from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Dino AWDP Platform"
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./awdp.db"


settings = Settings()
