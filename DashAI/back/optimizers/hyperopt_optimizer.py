from hyperopt import fmin, tpe, hp
from DashAI.back.optimizers.base_optimizer import BaseOptimizer
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
)


class HyperOptSchema(BaseSchema):
    max_evals: schema_field(
        int_field(gt=0),
        placeholder={"fixed_value": 10},
        description= "The parameter 'max_evals' is the quantity of trials per study. It must be of "
        "type positive integer.",
    )   # type: ignore

class HyperOptOptimizer(BaseOptimizer):
    
    SCHEMA = HyperOptSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]   
    def __init__(self):
        self.sampler=tpe.suggest
        self.max_evals=100

    def config(self,library_config):
        """
        Configure the optimizer.

        Args:
            library_config (dict[str, any]): Dict with the parameters for hyper-opt optimizer.

        """
        self.max_evals= library_config['n_trials']
        self.sampler = library_config['sampler']



    def search_space(self,hyperparams_data):
        """
        Configure the search space.

        Args:
            hyperparams_data (dict[str, any]): Dict with the range values for the possible search space

        Returns
        -------
            search_space: Dict with the information for the search space .
        """
        search_space={}

        for hyperparameter in hyperparams_data:
                if hyperparams_data[hyperparameter]['type']=='int':
                    min_value=hyperparams_data[hyperparameter]['minimum']
                    max_value=hyperparams_data[hyperparameter]['maximum']
                    step=hyperparams_data[hyperparameter]['step']
                    search_space[hyperparameter]=hp.quniform(str(hyperparameter),min_value,max_value,step)

                elif hyperparams_data[hyperparameter]['type']=='float':
                    min_value=hyperparams_data[hyperparameter]['minimum']
                    max_value=hyperparams_data[hyperparameter]['maximum']
                    step=hyperparams_data[hyperparameter]['step']
                    search_space[hyperparameter]=hp.uniform(min_value,max_value)

                else:
                    None
        return search_space


    def optimize(self, model,dataset,parameters, metric):

        """
        Optimization process

        Args:
            model (class): class for the model from the current experiment 
            dataset (dict): dict with the data to train and validation
            parameters (dict): dict with the information to create the search space
            metric (class): class for the metric to optimize

        Returns
        -------
            best_model: Object from the class model with the best hyperparameters found.
        """
        self.model=model
        self.dataset=dataset
        self.metric=metric
        self.parameters=parameters
        search_space=self.search_space(self.parameters)


        def objective(params):
            model_eval=self.model()
            model_eval.fit(self.dataset['train_input'], self.dataset['train_output'])
            y_pred = model_eval.predict(dataset['valid_input'])
            score = self.metric(dataset['valid_output'], y_pred)
            return score


        best_params = fmin(fn=objective, space=search_space, algo=self.sampler, max_evals=self.max_evals)

        for hyperparameter, value in best_params.items():
            if parameters[hyperparameter]["type"]=='int':
                best_params[hyperparameter]=int(value)
            else:
              None

        best_model= self.model()
        for hyperparameter, value in best_params.items():
            setattr(best_model, hyperparameter, value)

        best_model.fit(self.dataset['train_input'],self.dataset['train_output'])
        y_pred = best_model.predict(self.dataset['valid_input'])
        score = self.metric(self.dataset['valid_output'], y_pred)

        return best_model
