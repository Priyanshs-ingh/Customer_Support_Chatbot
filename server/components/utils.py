import pymongo

MONGODB_URI = "mongodb+srv://priyanshs042005:ZFHide2C0yDUKS76@nebula.zq7yzig.mongodb.net/Nebula?retryWrites=true&w=majority&appName=nebula"

class DataExtract():
    def __init__(self, database, collection):
        self.database = database
        self.collection = collection
        self.mongo_client = None
        self.db = None
        self.collection_instance = None
        self.connect_to_mongodb()

    def connect_to_mongodb(self):
        try:
            self.mongo_client = pymongo.MongoClient(MONGODB_URI)
            self.mongo_client.server_info()
            self.db = self.mongo_client[self.database]
            self.collection_instance = self.db[self.collection]
            print(f"Successfully connected to MongoDB: {self.database}.{self.collection}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def insert_data_mongodb(self, records):
        if not isinstance(records, list):
            records = [records]
        
        try:
            result = self.collection_instance.insert_many(records)
            return len(result.inserted_ids)
        except Exception as e:
            print(f"An error occurred while inserting data: {e}")

    def __del__(self):
        if self.mongo_client:
            self.mongo_client.close()