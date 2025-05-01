import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure

MONGODB_URI = "mongodb+srv://priyanshs042005:ZFHide2C0yDUKS76@nebula.zq7yzig.mongodb.net/?retryWrites=true&w=majority&appName=nebula"

class DataExtract():
    def __init__(self, database: str, collection: str):
        """
        Initializes the DataExtract class and attempts to connect to MongoDB.

        Args:
            database (str): The name of the database to connect to.
            collection (str): The name of the collection to use.
        """
        self.database_name = database
        self.collection_name = collection
        self.mongo_client = None
        self.db = None
        self.collection_instance = None
        self.connect_to_mongodb()

    def connect_to_mongodb(self):
        """Establishes a connection to the MongoDB database and collection."""
        try:
            self.mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ismaster')
            self.db = self.mongo_client[self.database_name]
            self.collection_instance = self.db[self.collection_name]
            print(f"Successfully connected to MongoDB: {self.database_name}.{self.collection_name}")
        except ConnectionFailure as e:
            print(f"MongoDB Connection Failure: Could not connect to MongoDB at {MONGODB_URI.split('@')[-1]}: {e}")
            self.mongo_client = None
            self.db = None
            self.collection_instance = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.mongo_client = None
            self.db = None
            self.collection_instance = None


    def insert_data_mongodb(self, records):
        """
        Inserts one or more records into the MongoDB collection.

        Args:
            records (dict or list): A single dictionary or a list of dictionaries representing the records.

        Returns:
            int: The number of successfully inserted documents, or 0 if an error occurred or connection failed.
        """
        # --- CORRECTED CHECK ---
        if self.collection_instance is None:
            print("Error: Cannot insert data, MongoDB collection not initialized (connection likely failed).")
            return 0
        # --- END CORRECTION ---

        if not isinstance(records, list):
            if isinstance(records, dict):
                records = [records]
            else:
                print("Error: Input 'records' must be a dictionary or a list of dictionaries.")
                return 0

        if not records:
            print("Warning: No records provided to insert.")
            return 0

        try:
            result = self.collection_instance.insert_many(records)
            print(f"Successfully inserted {len(result.inserted_ids)} records into {self.collection_name}.")
            return len(result.inserted_ids)
        except OperationFailure as e:
             print(f"An error occurred during MongoDB insert operation: {e.details}")
             return 0
        except Exception as e:
            print(f"An unexpected error occurred while inserting data: {e}")
            return 0


    def find_one(self, query: dict):
        """
        Finds a single document matching the specified query.

        Args:
            query (dict): The query criteria (e.g., {"email": "test@example.com"}).

        Returns:
            dict or None: The found document as a dictionary, or None if no document matches or an error occurs.
        """
        # --- CORRECTED CHECK ---
        if self.collection_instance is None:
            print("Error: Cannot find data, MongoDB collection not initialized (connection likely failed).")
            return None
        # --- END CORRECTION ---

        try:
            result = self.collection_instance.find_one(query)
            return result
        except OperationFailure as e:
             print(f"An error occurred during MongoDB find_one operation: {e.details}")
             return None
        except Exception as e:
            print(f"An unexpected error occurred during find_one: {e}")
            return None


    def __del__(self):
        """Closes the MongoDB connection when the object is destroyed."""
        if self.mongo_client:
            self.mongo_client.close()