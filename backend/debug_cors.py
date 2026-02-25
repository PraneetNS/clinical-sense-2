from app.core.config import settings
print(f"Type: {type(settings.BACKEND_CORS_ORIGINS)}")
print(f"Value: {settings.BACKEND_CORS_ORIGINS}")
for origin in settings.BACKEND_CORS_ORIGINS:
    print(f"Origin item: {origin}")
