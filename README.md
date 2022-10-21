# DashAI
DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models

## Instalation

### Dependencies

DashAI requires:

- Python (>= 3.8)
- FastAPI (>= 0.79.0)
- SQLAlchemy (>=1.4.36)
- scikit-learn (>=1.0.2)

### User Installation

If you already have Python installed, you need to clone this repository using

    git clone -b back/initial-api https://github.com/OpenCENIA/DashAI.git

The -b option is to clone only the `back/initial-api` branch, which is for now the stable branch of the project.

Next, you have to go to the root of the project using:

    cd DashAI

After that you need to install the dependencies, for that you can use in the root of the project:

    sh init.sh

You are now ready to train, evaluate and play with all the models provided by DashAI.

## Usage

To run the web user interface just use:

    sh run.sh

Open your browser at [localhost](http://localhost:3000/) and navigate through the user-friendly interface.
