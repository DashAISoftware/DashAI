from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name='DashAI',
    packages=find_packages(),
    include_package_data=True,
    version='0.0.4',
    license='MIT',
    description='DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Felipe Bravo-Marquez',
    author_email='fbravo@dcc.uchile.cl',
    url='https://github.com/OpenCENIA/DashAI',
    install_requires=[
        'fastapi[all]',
        'SQLAlchemy',
        'scikit-learn'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=['dashai'],
)
