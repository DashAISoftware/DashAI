import optuna
from DashAI.back.optimizers.base_optimizer import BaseOptimizer
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
)


class OptunaSchema(BaseSchema):
    n_trials: schema_field(
        int_field(gt=0),
        placeholder=10,
        description= "The parameter 'n_trials' is the quantity of trials per study. It must be of "
        "type positive integer.",
    )   # type: ignore

class OptunaOptimizer(BaseOptimizer):
    
    SCHEMA= OptunaSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]
    
    def __init__(self):
        self.study=optuna.create_study(direction='maximize')
        self.n_trials=None
        self.n_sampler=None
        self.pruner=None
        self.study_name=None

    def config(self,library_config):
        self.n_trials= library_config['n_trials']
        self.sampler = library_config['sampler']
        self.pruner = library_config['pruner']
        self.study_name = library_config['study_name']
        self.study=optuna.create_study(direction='maximize',sampler=self.sampler,pruner=self.pruner,study_name=self.study_name)
        """
        Configure the optimizer.

        Args:
            library_config (dict[str, any]): Dict with the parameters for optuna optimizer.

        """
    
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
            min_value=hyperparams_data[hyperparameter]['minimum']
            max_value=hyperparams_data[hyperparameter]['maximum']
            search_space[hyperparameter]=list(range(min_value,max_value))

        return search_space
    

    def optimize(self, model , dataset , parameters , metric):
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
        self.parameters=parameters
        self.metric=metric
        search_space=self.search_space(self.parameters)

        def objective(trial):
            model_trial=self.model()
            for hyperparameter, valores in search_space.items():
                if parameters[hyperparameter]['type']=='int':
                    value = trial.suggest_int(hyperparameter, valores[0],valores[-1])
                    setattr(model_trial, hyperparameter, value)
                elif parameters[hyperparameter]['type']=='int':
                    value = trial.suggest_float(hyperparameter, valores[0],valores[-1])
                    setattr(model_trial, hyperparameter, value)
                else:
                    None

            model_trial.fit(self.dataset['train_input'], self.dataset['train_output'])
            y_pred = model_trial.predict(dataset['valid_input'])
            score = self.metric(dataset['valid_output'], y_pred)

            return score


        self.study.optimize(objective, n_trials=self.n_trials)

        best_params = self.study.best_params
        best_model= self.model()
        for hyperparameter, value in best_params.items():
            setattr(best_model, hyperparameter, value)
        best_model.fit(self.dataset['train_input'], self.dataset['train_output'])
        y_pred = best_model.predict(dataset['valid_input'])
        score = self.metric(dataset['valid_output'], y_pred)

        return best_model