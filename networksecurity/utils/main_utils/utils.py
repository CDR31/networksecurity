import yaml
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
import sys,os
import numpy as np
import dill
import pickle
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
def read_yaml_file(file_path:str)->dict:
    try:
        with open(file_path,'rb') as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e

def write_yaml_file(file_path:str,content:object,replace:bool = False)->None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,'w') as file:
            yaml.dump(content,file)

    except Exception as e:
        raise NetworkSecurityException(e,sys)

def save_numpy_array_data(file_path:str,array:np.array):

    """
    Save numpy array data to file
    file_path: str location of file to save
    array:np.array data to save
    """
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)
        with open(file_path,'wb') as file_obj:
            np.save(file_obj,array)

    except Exception as e:
        raise NetworkSecurityException(e,sys) from e

def save_object(file_path:str,obj:object)->None:
    try:
        logging.info("Entered the save_object method of MainUtils class")
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,'wb') as file_obj:
            pickle.dump(obj,file_obj)
        logging.info("Exited the save_object method of mainUtils class")
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e


def load_object(file_path:str,)->object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} is not exists")
        with open(file_path,"rb") as file_obj:
            print(file_obj)

            return pickle.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e

def load_numpy_array_data(file_path:str)-> np.array:
    """
    Load numpy array data fro file file_path:str loaction of file to load
    return: np.array data loaded
    """
    try:
        with open(file_path,'rb') as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise NetworkSecurityException(e,sys) from e
def evaluate_models(x_train, y_train, x_test, y_test, models, param):
    try:
        report = {}

        for i in range(len(list(models))):

            model_name = list(models.keys())[i]
            model = list(models.values())[i]
            para = param[model_name]

            # If parameters are provided, perform GridSearchCV
            if para:

                gs = GridSearchCV(
                    model,
                    para,
                    cv=3,
                    n_jobs=-1
                )

                gs.fit(x_train, y_train)

                # Get the best fitted model
                model = gs.best_estimator_

            else:
                # No hyperparameter tuning
                model.fit(x_train, y_train)

            # Store the fitted/best model back into dictionary
            models[model_name] = model

            # Training prediction
            y_train_pred = model.predict(x_train)

            # Testing prediction
            y_test_pred = model.predict(x_test)

            # Calculate R2 score
            train_model_score = f1_score(
            y_train,
            y_train_pred,
            average='weighted'
            )

            test_model_score = f1_score(
            y_test,
            y_test_pred,
            average='weighted'
            )

            report[model_name] = test_model_score

            print(f"{model_name}:")
            print(f"Train Score: {train_model_score}")
            print(f"Test Score: {test_model_score}")
            print("-" * 50)

        return report

    except Exception as e:
        raise NetworkSecurityException(e, sys)