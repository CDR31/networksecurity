from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import dataingestionconfig,DataValidationConfig
from networksecurity.entity.config_entity import Trainingpipelineconfig
import sys

if __name__ == "__main__":
    try:
        trainingpipelineconfig = Trainingpipelineconfig()
        data_ingestion_config = dataingestionconfig(trainingpipelineconfig)
        data_ingestion = DataIngestion(Data_Ingestion_Config=data_ingestion_config)
        logging.info("Initiating the data ingestion process.")
        dataingestionartifact = data_ingestion.initiate_data_ingestion()
        logging.info('Data Ingestion Completed.')
        print(dataingestionartifact)
        data_validation_config = DataValidationConfig(trainingpipelineconfig)
        data_validation = DataValidation(dataingestionartifact,data_validation_config)
        logging.info('Initiate the data validation')
        data_validation_artifact = data_validation.initiate_date__validation()
        logging.info('data validation completed')
        print(data_validation_artifact)
        
        
    except Exception as e:
        raise NetworkSecurityException(e,sys)