from setuptools import find_packages, setup

# To install extra package from local by using direct references. 
# In production, this should be installed from pypi
import os
path_to_my_project = f"{os.getcwd()}/plugins/tabular_plugin"

with open("README.rst") as f:
    long_description = f.read()

requirements = [
    "fastapi>=0.88",
    "SQLAlchemy>=2.0",
    "numpy>=1.17.3",
    "joblib>=1.1.1",
    "pydantic>=1.10.5",
    "starlette>=0.25.0,<0.26.0",
    "scikit-learn>=1.2.1",
    "datasets>=2.9.0",
    "evaluate>=0.4.0",
]

extra_requirements = {
    'transformers': [
        'transformers>=4.23.1',
        'sacrebleu>=2.3.1',
        'sentencepiece>=0.1.97',
    ],
    # Direct reference: https://peps.python.org/pep-0440/#direct-references
    'tabular': [f"tabular_plugin @ file://localhost/{path_to_my_project}#egg=tabular_plugin"]
    # 'tabular': "tabular_plugin" # This should be the corrent in production
}

test_requirements = [
    "pytest>=7.1.2",
]


setup(
    name="DashAI",
    version="0.0.4",
    license="MIT",
    description="DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models.",
    long_description=long_description,
    url="https://github.com/OpenCENIA/DashAI",
    project_urls={
        "Documentation": "https://DashAI.readthedocs.io/",
        "Changelog": "https://DashAI.readthedocs.io/en/latest/changelog.html",
        "Issue Tracker": "https://github.com/DashAISoftware/DashAI/issues",
    },
    author="DashAI Team",
    author_email="fbravo@dcc.uchile.cl",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require=extra_requirements,
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
            "dashai = DashAI:run",
        ]
    },
)
