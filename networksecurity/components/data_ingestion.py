from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

## configuration of the data ingestion config

from networksecurity.entity.config_entity import dataingestionconfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact

import os
import sys

import certifi
import pymongo
import pandas as pd
import numpy as np

from typing import List
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

if not MONGO_DB_URL:
    raise ValueError(
        "MONGO_DB_URL is missing from the environment. "
        "Please check your .env file."
    )

client = pymongo.MongoClient(
    MONGO_DB_URL,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=15000,
)

client.admin.command("ping")

print("MongoDB Atlas connection successful!")




class DataIngestion:
    def __init__(self, data_ingestion_config: dataingestionconfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def export_collection_as_dataframe(self):
        """This function exports the data from the MongoDB collection as a pandas DataFrame."""


        try:
            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
            collection = self.mongo_client[database_name][collection_name]  
            df = pd.DataFrame(list(collection.find()))

            if "_id" in df.columns.to_list():
                df = df.drop(columns=["_id"])

            df.replace({'na':np.nan},inplace=True)
            return df

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def export_data_into_feature_store(self, dataframe:pd.DataFrame):
        """This function exports the data into the feature store as a CSV file."""
        try:
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(feature_store_file_path, index=False, header=True)
            return dataframe
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def split_data_as_train_test(self, dataframe:pd.DataFrame):
        """This function splits the data into train and test datasets and saves them as CSV files."""
        try:
            train_set, test_set = train_test_split(dataframe, test_size=self.data_ingestion_config.train_test_split_ratio, random_state=42)
            logging.info('Performed train test split on the dataframe')
            logging.info('Exited split_data_as_train_test method of the data_ingestion class')

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path,exist_ok=True)

            logging.info(f"Explorting train and test file path.")
            train_set.to_csv(self.data_ingestion_config.training_file_path, index=False, header=True)
            test_set.to_csv(self.data_ingestion_config.testing_file_path, index=False, header=True)
            logging.info(f"Exported train and test file paths.")

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_ingestion(self):
        try:
            dataframe = self.export_collection_as_dataframe()
            dataframe = self.export_data_into_feature_store(dataframe)
            self.split_data_as_train_test(dataframe=dataframe)
            dataingestionartifact = DataIngestionArtifact(train_file_path = self.data_ingestion_config.training_file_path, test_file_path = self.data_ingestion_config.testing_file_path)
            return dataingestionartifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)