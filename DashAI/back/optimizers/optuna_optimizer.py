import optuna
from optuna.samplers import TPESampler, CmaEsSampler
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
    sampler: schema_field(
        enum_field(enum=["TPESampler", "CmaEsSampler"]),
        placeholder="TPESampler",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels. Must be in "
        "string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    pruner: schema_field(
        enum_field(enum=["MedianPruner", "None"]),
        placeholder="None",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels. Must be in "
        "string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    metric: schema_field(
        enum_field(enum=["Accuracy","F1Score"]),
        placeholder="Accuracy",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels. Must be in "
        "string format and can be 'scale' or 'auto'.",
    )  # type: ignore

class OptunaOptimizer(BaseOptimizer):
    
    SCHEMA= OptunaSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]
    
    def __init__(self,n_trials=None,sampler=None,pruner=None,metric=None):
        self.n_trials=n_trials
        self.sampler=getattr(optuna.samplers,sampler)
        self.pruner=pruner
        self.metric=metric
    
    # def search_space(self,hyperparams_data):
    #     """
    #     Configure the search space.

    #     Args:
    #         hyperparams_data (dict[str, any]): Dict with the range values for the possible search space

    #     Returns
    #     -------
    #         search_space: Dict with the information for the search space .
    #     """
    #     search_space={}
    #     for hyperparameter in hyperparams_data:
    #         lower_bound=hyperparams_data[hyperparameter][0]
    #         upper_bound=hyperparams_data[hyperparameter][1]
    #         search_space[hyperparameter]=list(range(lower_bound,upper_bound))

    #     return search_space
    

    def optimize(self, model , input_dataset, output_dataset, parameters):
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
        self.input_dataset=input_dataset
        self.output_dataset=output_dataset
        self.parameters=parameters
        # search_space=self.search_space(self.parameters)
        
        if self.metric['name'] in ["Accuracy", "F1", "Precision", "Recall"]:
            study=optuna.create_study(direction='maximize',sampler=self.sampler(),pruner=self.pruner)
        else:
            study=optuna.create_study(direction='minimize',sampler=self.sampler(),pruner=self.pruner)
        
        self.metric=self.metric['class']
        

        def objective(trial):
            model_trial=self.model
            for hyperparameter, values in self.parameters.items():
                # if parameters[hyperparameter]['type']=='int':
                value = trial.suggest_int(hyperparameter, values[0],values[-1])
                setattr(model_trial, hyperparameter, value)
                # elif parameters[hyperparameter]['type']=='float':
                #     value = trial.suggest_float(hyperparameter, values[0],values[-1])
                #     setattr(model_trial, hyperparameter, value)
                # else:
                #     None

            model_trial.fit(self.input_dataset['train'], self.output_dataset['train'])
            y_pred = model_trial.predict(input_dataset['validation'])
            score = self.metric.score(output_dataset['validation'], y_pred)

            return score


        study.optimize(objective, n_trials=self.n_trials)

        best_params = study.best_params
        best_model= self.model
        for hyperparameter, value in best_params.items():
            setattr(best_model, hyperparameter, value)
        best_model.fit(self.input_dataset['train'], self.output_dataset['train'])
        self.model=best_model
        
    def get_model(self):
        return self.model
        # y_pred = best_model.predict(input_dataset['validation'])
        # score = self.metric(output_dataset['validation'], y_pred)
