from setuptools import setup

setup(
    name='DashAI',
    packages=['back'],
    version='0.0.3',
    license='MIT',
    description='DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models.',
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
