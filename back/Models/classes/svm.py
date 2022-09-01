import json

from sklearn.svm import SVC

from Models.classes.numericClassificationModel import NumericClassificationModel
from Models.classes.sklearnLikeModel import SkleanLikeModel


class SVM(SkleanLikeModel, NumericClassificationModel, SVC):
    """
    Support vector machine. Supervised learning algorithm that separates
    two classes in two spaces by means of a hyperplane. This hyperplane is
    defined as a vector called support vector.
    """

    MODEL = "svm"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    # def __init__(self, **kwargs):

    #     """
    #     Kwargs:
    #         preprocess (Preprocess): preprocesamiento instanciado,
    #         que contiene parámetros y tokenizadores inicializados.
    #         params (dic): diccionario que contiene los hiperparámetros que
    #                         utiliza el modelo.

    #     params (dict):
    #         probability (bool): True si se quiere predecir
    #         por probabilidades. Default: True.
    #         kernel (str): linear, poly, rbf, sigmoid.
    #         Es el kernel a utilizar en el modelo. Default=rbf
    #         gamma (str o float): scale, auto} o float, default=’scale’.
    #         Coeficiente para los kernels rbf, poly y sigmoid.
    #         coef0 (float): Default=0.0. Valor independiente del kernel.
    #         Solo es significante para kernel poly y sigmoid.
    #     """

    #     preprocess = kwargs.get('preprocess', None)
    #     if preprocess is None:
    #         preprocess = DistilBertEmbedding(
    #             {'params': {}, 'tokenizer': []})
    #     super().__init__(preprocess)

    #     self.params = kwargs.get('params', {})
    #     self.params['probability'] = self.params.get('probability', True)
    #     self.params['kernel'] = self.params.get('kernel', 'rbf')
    #     self.params['gamma'] = self.params.get('gamma', 0.1)

    #     self.kwargs = kwargs
    #     self.ml_svm = OneVsRestClassifier(SVC(**self.params))

    # def fit(self, x, y=None):
    #     """
    #     Método que se usa para entrenar el modelo, no debe retornar nada.

    #     x (array-like): Arreglo donde cada componente tiene un texto
    #     ya preprocesado por el preprocess.
    #     y (array-like): Arreglo donde cada componente tiene un arreglo
    #     binario indicando si se prensenta o no la label
    #     """

    #     self.ml_svm.fit(x, y)

    # def predict(self, x):
    #     """
    #     Método que se usa para predecir.

    #     x (array-like): Arreglo donde cada componente tiene un texto ya
    #                         preprocesado por preprocess.

    #     Retorna matriz de adyacencia, que indica la pertenencia de
    #     de las labels a las sentencias. En las filas se
    #     representan las sentencias (en orden), y en las
    #     columnas las etiquetas (en orden).
    #     """
    #     return self.ml_svm.predict(x)

    # def predict_proba(self, X):
    #     """
    #     Este método es posible de realizar cuando 'probability = True'.
    #     Entrega la probabilidad de que cada etiqueta pertenezca a las
    #     distintas sentencias.

    #     X (array-like): Arreglo donde cada componente tiene un texto ya
    #                     preprocesado por preprocess.

    #     Retorna dataFrame, donde cada sentencia es representada
    #     en una fila, y en cada columna se representa una
    #     etiqueta. En la entrada (m,n) se puede observar la
    #     probabilidad de que en la m-ésima sentencia esté
    #     la n-ésima etiqueta.
    #     """
    #     aux = pd.DataFrame(self.ml_svm.predict_proba(X))
    #     return aux
