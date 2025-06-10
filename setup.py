from setuptools import setup, find_packages

setup(
    name="signaldrift",
    version="0.1.0",
    description="Sports betting arbitrage and market-making system",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "jupyter>=1.0.0",
        "notebook>=7.0.7",
        "numpy>=1.26.4",
        "pandas>=2.2.1",
        "matplotlib>=3.8.3",
        "py-clob-client",
        "pytest>=8.3.2",
        "selenium>=4.25.0",
        "requests>=2.32.3",
        "beautifulsoup4>=4.12.3",
        "plotly>=5.0.0",
        "ipywidgets>=8.0.0",
        "nest-asyncio>=1.5.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
        ]
    },
)