import os
import httpx
import asyncio
from pathlib import Path

MODELS_DIR = Path(".models")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

async def download_file(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"{dest} already exists. Skipping download.")
        return
        
    print(f"Downloading {url} to {dest}...")
    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
    print(f"Downloaded {dest}")

async def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    
    await asyncio.gather(
        download_file(MODEL_URL, MODELS_DIR / "kokoro-v1.0.onnx"),
        download_file(VOICES_URL, MODELS_DIR / "voices-v1.0.bin")
    )
    print("Done downloading models.")

if __name__ == "__main__":
    asyncio.run(main())
