from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
# Remove OAuth2PasswordRequestForm import if no longer needed elsewhere
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer # Keep this for dependency injection
from pydantic import BaseModel, EmailStr # Use EmailStr for validation
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
from core import run_customer_support # Assuming core.py is in the same directory or accessible
from config import ALLOWED_ORIGINS # Assuming config.py is setup
from components.utils import DataExtract # Assuming components/utils.py is setup

# JWT configuration - !! STORE THIS SECURELY IN PRODUCTION (e.g., env vars) !!
SECRET_KEY = "e64c2a556b75837f0991dfd5586e48b6e454bc9253c5744be9e7c0e00e18d61d7bfeb0846e3684f6ae0661ef595661d9002677b801668324a818d88658bb997d0e40bac6b821c43584f9c99e4890330d09561ff992ed2d19d609d976582fc23909f74bd8ea97540d54bc0a725c328c6d9aaea13f1120523e42d6c9a4875dc827e2ec4a758fccb11441459973798fbc8b6ba23a20eee1611f45fc05103812e133165ea62a918fc5c5d32db4c8701510019e7c741ab9cbc48c5e0b3b66688a1cfa7f3800eff12c29a2dca24fc4a7116e7fcd1c10e28f6b1212e5cfb5704a5115f573d169360ec58d894b85b9e01ebf416a4ba9d8b579cef3576ce1f212ea597cd6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, # Use the list from config.py
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods including OPTIONS, POST, GET etc.
    allow_headers=["*"], # Allows all headers including Authorization, Content-Type
)

# --- Database Setup ---
database = "nebula" # Example DB name

# --- Security Scheme ---
# The tokenUrl should match the *exact* path of your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Corrected path

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str

class DataRequest(BaseModel):
    records: List[Dict[str, Any]]
    database: str
    collection: str

class UserBase(BaseModel):
    email: EmailStr # Use EmailStr for automatic validation

class UserCreate(UserBase):
    password: str

# This model is used for the JSON request body of the login endpoint
class UserLogin(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: str # Expecting stringified _id
    # Add other fields you want to return about the user, except password
    created_at: Optional[datetime] = None

class UserInDB(UserInDBBase):
     # If you have more fields specific to DB representation
     pass


class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class Token(BaseModel):
    token: str
    ok: bool = True # Optional field to indicate success
    user: UserInDB # Return user info based on UserInDB model

# --- Helper Functions ---
def get_password_hash(password: str) -> str:
    # ... (keep existing function)
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # ... (keep existing function)
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except ValueError:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # ... (keep existing function)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    # ... (keep existing function)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            print("Token payload missing 'sub' (email)")
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        print(f"JWT decoding error: {e}")
        raise credentials_exception

    try:
        data_extractor = DataExtract(database=database, collection="users")
        user_dict = data_extractor.find_one({"email": token_data.email})
    except Exception as e:
        print(f"Database error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error accessing user data"
        )

    if user_dict is None:
        print(f"User not found in DB for token validation: {token_data.email}")
        raise credentials_exception

    # Prepare user dict for return (convert _id, remove password)
    if "_id" in user_dict:
        user_dict["id"] = str(user_dict["_id"])
        del user_dict["_id"]
    if "password" in user_dict:
        del user_dict["password"]

    return user_dict


# --- API Routes ---

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED, response_model=Dict[str, str])
async def register(user: UserCreate):
    # ... (keep existing function)
    try:
        data_extractor = DataExtract(database=database, collection="users")

        existing_user = data_extractor.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(user.password)

        new_user_doc = {
            "email": user.email,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }

        inserted_count = data_extractor.insert_data_mongodb([new_user_doc])

        if inserted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

        print(f"User registered successfully: {user.email}") # Log success
        return {"message": "User registered successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error during registration for {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration."
        )


# --- CORRECTED LOGIN ROUTE ---
@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin): # Expect UserLogin model (JSON)
    """
    Authenticates a user based on email and password provided in JSON body.
    Returns a JWT token and user information upon success.
    """
    email = user_credentials.email
    password = user_credentials.password
    print(f"Login attempt for email: {email}") # Log login attempt

    try:
        data_extractor = DataExtract(database=database, collection="users")

        # Find user
        db_user_dict = data_extractor.find_one({"email": email})
        if not db_user_dict:
            print(f"Login attempt failed: User not found - {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, # Use 401 for failed auth
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        stored_hashed_password = db_user_dict.get("password", "")
        if not verify_password(password, stored_hashed_password):
            print(f"Login attempt failed: Invalid password - {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, # Use 401 for failed auth
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Password verified, create token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        print("Token" ,access_token)
        print(f"Login successful, token created for: {email}")

        # Prepare user info for response using the UserInDB model
        # Make sure all fields required by UserInDB are present in db_user_dict or handled
        user_info_for_token = UserInDB(
            id=str(db_user_dict.get("_id")), # Convert ObjectId
            email=db_user_dict.get("email"),
            created_at=db_user_dict.get("created_at")
            # Add other fields from UserInDB model if necessary
        )

        return Token(token=access_token, user=user_info_for_token, ok=True)

    except HTTPException as http_exc:
        # Re-raise exceptions with specific status codes
        raise http_exc
    except Exception as e:
        print(f"Unexpected error during login for {email}: {e}")
        # Log traceback for debugging unexpected errors
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred during login."
        )
# --- END OF CORRECTED LOGIN ROUTE ---


@app.get("/api/auth/verify-token", response_model=UserInDB)
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    # ... (keep existing function)
    try:
        # Ensure current_user dict keys match UserInDB model fields
        return UserInDB(**current_user)
    except Exception as e:
         print(f"Error creating UserInDB model from current_user dict: {e}")
         print(f"Current user dict was: {current_user}")
         raise HTTPException(status_code=500, detail="Error processing user data")


# This endpoint might need protection depending on its use case
@app.post("/api/create-user", status_code=status.HTTP_201_CREATED)
async def insert_data(request: DataRequest): # Removed Depends(get_current_user) unless needed
    # ... (keep existing function, ensure DataExtract usage is correct)
    try:
        collection = request.collection or "users" # Be careful allowing arbitrary collections
        data_extractor = DataExtract(database=request.database, collection=collection)

        records_to_insert = []
        for record in request.records:
            if "password" in record:
                record["password"] = get_password_hash(record["password"])
            if "created_at" not in record:
                 record["created_at"] = datetime.utcnow()
            records_to_insert.append(record)

        if not records_to_insert:
             raise HTTPException(status_code=400, detail="No valid records provided")

        inserted_count = data_extractor.insert_data_mongodb(records_to_insert)
        return {"message": f"Successfully inserted {inserted_count} records into {collection}"}
    except Exception as e:
        print(f"Error in insert-data endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=Dict[str, Any]) # Define response better if possible
async def chat(request: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    # ... (keep existing function)
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message received")

        user_id = current_user.get("id")
        if not user_id:
             # This shouldn't happen if get_current_user worked, but good check
             raise HTTPException(status_code=401, detail="Could not identify authenticated user")

        print(f"Received message from user {user_id} ({current_user.get('email')}): {request.message}")

        result = run_customer_support(request.message)
        if not result or not isinstance(result, dict) or 'response' not in result:
            print(f"Workflow 'run_customer_support' returned invalid result: {result}")
            raise HTTPException(status_code=500, detail="Chat processing failed internally")

        # Prepare chat data for saving
        chat_data = {
            "user_id": user_id,
            "email": current_user.get("email"),
            "message": request.message,
            "response": result.get("response"),
            "category": result.get("category"), # Store if available
            "sentiment": result.get("sentiment"), # Store if available
            "timestamp": datetime.utcnow()
        }

        try:
            chat_log_extractor = DataExtract(database=database, collection="chats")
            # Ensure DataExtract is initialized correctly for 'chats' collection
            if chat_log_extractor.collection_instance is not None:
                 chat_log_extractor.insert_data_mongodb([chat_data])
                 print("Chat log saved successfully.")
            else:
                 print("WARNING: Failed to initialize DataExtract for chat logs. Log not saved.")
        except Exception as db_error:
            print(f"ERROR: Failed to save chat log: {db_error}")
            # Log and continue, don't fail the chat response for this

        print(f"Sending response: {result}")
        # Return the raw result dict from the core logic
        return result

    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        print(f"Error in chat endpoint for user {current_user.get('email')}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred in chat.")


@app.get("/health")
async def health():
    # Optional: Add a quick check to MongoDB here if desired
    # try:
    #     client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    #     client.admin.command('ping')
    #     db_status = "connected"
    # except Exception:
    #     db_status = "disconnected"
    # return {"status": "ok", "database": db_status}
    return {"status": "ok"}

# --- Run Application ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    # Make sure host and port match what frontend expects
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)