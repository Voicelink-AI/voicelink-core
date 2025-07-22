from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
    BUILD_ID = os.getenv("BUILD_ID", "VCLNK-9")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")