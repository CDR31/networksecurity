from pymongo.mongo_client import MongoClient

MONGO_DB_URL = "mongodb+srv://pankajraj2025434_db_user:Pankaj8817@cluster0.bxf1lxu.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_DB_URL)

try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")

except Exception as e:
    print("MongoDB connection failed:")
    print(e)
