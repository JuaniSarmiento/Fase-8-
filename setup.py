"""
Setup script for AI-Native MVP V3

Allows installation in development mode with: pip install -e .
"""
from setuptools import setup, find_packages

setup(
    name="ai-native-mvp-v3",
    version="3.0.0",
    description="AI-Native Learning Platform with Clean Architecture",
    author="AI-Native Team",
    packages=find_packages(exclude=["Test", "Test.*"]),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.115.6",
        "uvicorn[standard]>=0.34.0",
        "pydantic>=2.10.5",
        "pydantic-settings>=2.7.1",
        "sqlalchemy>=2.0.37",
        "asyncpg>=0.30.0",
        "alembic>=1.14.0",
        "psycopg2-binary>=2.9.10",
        "redis>=5.2.1",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.20",
        "httpx>=0.27.0,<0.28.0",
        "prometheus-client>=0.21.1",
        "prometheus-fastapi-instrumentator>=7.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=8.3.4",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=6.0.0",
            "httpx>=0.27.0",
            "aiosqlite>=0.20.0",
        ],
        "llm": [
            "openai>=1.59.8",
            "anthropic>=0.42.0",
            "google-generativeai>=0.8.3",
            "langchain>=0.3.17",
            "langchain-community>=0.3.16",
            "langchain-openai>=0.2.14",
            "langchain-anthropic>=0.3.5",
            "chromadb>=0.5.23",
            "sentence-transformers>=3.3.1",
        ],
    },
)
