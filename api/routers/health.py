from fastapi import APIRouter, HTTPException
from fastapi import status
from ..config import Config
import httpx


router = APIRouter()

@router.get("/health")
async def is_ethereum_alive() -> bool:  # (1)!
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                Config.ETHEREUM_RPC_URL,
                json={"jsonrpc": "2.0", "method": "web3_clientVersion", "id": 1}
            )
            return response.status_code == 200
    except Exception:
        return False

async def is_elevenlabs_alive() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.elevenlabs.io/v1/models",
                headers={"xi-api-key": Config.ELEVENLABS_API_KEY}
            )
            return response.status_code == 200
    except Exception:
        return False

@router.get("/")
async def health_check():
    ethereum_ok = await is_ethereum_alive()
    elevenlabs_ok = await is_elevenlabs_alive()

    if not all([ethereum_ok, elevenlabs_ok]):  # (2)!
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "ERROR",
                "dependencies": {
                    "ethereum_rpc": ethereum_ok,
                    "elevenlabs_api": elevenlabs_ok
                }
            }
        )

    return {  # (3)!
        "status": "OK",
        "dependencies": {
            "ethereum_rpc": ethereum_ok,
            "elevenlabs_api": elevenlabs_ok
        }
    }