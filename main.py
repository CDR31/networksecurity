from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import dataingestionconfig
from networksecurity.entity.config_entity import Trainingpipelineconfig
import sys

if __name__ == "__main__":
    try:
        trainingpipelineconfig = Trainingpipelineconfig()
        data_ingestion_config = dataingestionconfig(trainingpipelineconfig)
        data_ingestion = DataIngestion(Data_Ingestion_Config=data_ingestion_config)
        logging.info("Initiating the data ingestion process")
        dataingestionartifact = data_ingestion.initiate_data_ingestion()
        print(dataingestionartifact)
        
    except Exception as e:
        raise NetworkSecurityException(e,sys)