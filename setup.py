from setuptools import setup, find_packages

setup(
    name="voicelink-core",
    version="1.0.0",
    description="AI-powered voice-to-documentation pipeline",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "openai>=1.0.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "voicelink-server=api.main:app",
            "voicelink-process=scripts.test_complete_voicelink_demo:run_complete_demo",
        ],
    },
)
