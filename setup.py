"""
Setup script for ScreenAI Test Automation Tool
"""
from setuptools import setup, find_packages

setup(
    name="screenai-test-automation",
    version="1.0.0",
    description="UI test automation using OmniParser and Maestro",
    author="ScreenAI Team",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.1",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "transformers>=4.30.0",
        "ultralytics>=8.0.0",
        "Pillow>=10.0.0",
        "PyYAML>=6.0",
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "fuzzywuzzy>=0.18.0",
        "python-Levenshtein>=0.21.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "huggingface-hub>=0.17.0",
    ],
    entry_points={
        "console_scripts": [
            "screenai=src.main:main",
        ],
    },
    python_requires=">=3.8",
)