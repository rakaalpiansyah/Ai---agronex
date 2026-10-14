import uvicorn
from config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print("=" * 70)
    print(f" Memulai {settings.app_name} v{settings.app_version}")
    print(" API Endpoint:    http://localhost:8000")
    print(" Dokumentasi API: http://localhost:8000/docs (Swagger UI)")
    print("=" * 70)
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
