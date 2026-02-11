import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
