from DashAI.back.metrics.classification_metric import ClassificationMetric

# # Obtener el índice de la clase con la probabilidad más alta
# max_index = np.argmax(probabilities)
#
# # Obtener la etiqueta correspondiente al índice
# predicted_label = clf.classes_[max_index]


class Accuracy(ClassificationMetric):
    def __init__(self, true_labels, pred_labels):
        self.true_labels = true_labels
        self.pred_labels = pred_labels

    # def transform_prob_to_labels(self, pred_labels):
