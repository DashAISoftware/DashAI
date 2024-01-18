from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()

requirements = [
    "fastapi[all]>=0.96",
    "SQLAlchemy>=2.0",
    "numpy>=1.17.3",
    "joblib>=1.2.0",
    "pydantic>=2.0.2",
    "pydantic-settings>=2.0.1",
    "starlette>=0.27.0,<0.28.0",
    "scikit-learn>=1.2.1",
    "datasets>=2.9.0",
    "evaluate>=0.4.0",
    "accelerate>=0.20.3",
    "torch==1.13.0",
    "transformers>=4.23.1",
    "sacrebleu>=2.3.1",
    "sentencepiece>=0.1.97",
]


test_requirements = [
    "pytest>=7.1.2",
    "hypothesis==6.52.1",
    "pre-commit>=2.20.0",
    "ruff>=0.0.218",
    "black>=23.1.0",
    "isort>=5.12.0",
    "sphinx_rtd_theme==1.2.0",
    "sphinx==6.1.3",
    "flake8>=6.0.0",
    "Flake8-pyproject>=1.2.2",
    "sqlalchemy-stubs>=0.4",
    "pytest-cov>=2.8.1",
    "httpx>=0.23.3",
    "ipdb==0.13.11",
    "pytest-cov==4.0.0",
]


setup(
    name="DashAI",
    version="0.0.14",
    license="MIT",
    description=(
        "DashAI: a graphical toolbox for training, evaluating and deploying "
        "state-of-the-art AI models."
    ),
    long_description=long_description,
    url="https://github.com/OpenCENIA/DashAI",
    project_urls={
        "Documentation": "https://dash-ai.com/",
        "Changelog": "https://dash-ai.com/changelog.html",
        "Issue Tracker": "https://github.com/DashAISoftware/DashAI/issues",
    },
    author="DashAI Team",
    author_email="fbravo@dcc.uchile.cl",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=requirements,
    test_require=test_requirements,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "dashai = DashAI:main",
        ]
    },
)
