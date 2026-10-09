# from pymongo.mongo_client import MongoClient
# MONGO_DB_URL = "mongodb+srv://pankajraj2025434_db_user:Pankaj8817@cluster0.bxf1lxu.mongodb.net/?appName=Cluster0" 
# client = MongoClient(MONGO_DB_URL) 
# try:     
#     client.admin.command("ping")     
#     print("Pinged your deployment. You successfully connected to MongoDB!") 
# except Exception as e:     
#     print("MongoDB connection failed:")     
# print(e)

import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

if not MONGO_DB_URL:
    raise ValueError(
        "MONGO_DB_URL is missing from your .env file."
    )

client = None

try:
    client = MongoClient(
        MONGO_DB_URL,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=15000
    )

    client.admin.command("ping")

    print("MongoDB Atlas connection successful!")

except Exception as e:
    print("MongoDB connection failed.")
    print("Error type:", type(e).__name__)
    print("Error details:", str(e))

finally:
    if client is not None:
        client.close()