
## 4. Core Components Explained

### 4.1. Frontend (Client - React)

*   **`main.jsx`:** Initializes the React application and sets up the `react-router-dom` browser router. It defines the main routes (`/login`, `/signup`, `/app`). Crucially, it includes a basic `isLoggedIn` check using `localStorage` *before* rendering the protected `/app` route, redirecting to `/login` if the flag isn't set.
*   **`App.jsx`:**
    *   Defines the `AuthContext` and `AuthProvider`. This is central to managing the user's authentication state (user object, token, loading status) across the application.
    *   `AuthProvider` handles:
        *   Storing/retrieving the token from `localStorage`.
        *   Verifying the token on initial load by calling the `/api/auth/verify-token` backend endpoint.
        *   Providing `login` and `logout` functions that update the context state and `localStorage`.
    *   Contains the main `Chatbot` component which:
        *   Renders the chat interface (header, message area, input form).
        *   Manages the conversation state (`messages`, `input`, `isBotLoading`).
        *   Handles sending user messages to the `/api/chat` backend endpoint, including the JWT in the `Authorization` header.
        *   Receives and displays responses from the backend.
        *   Provides a Logout button that calls `auth.logout()`.
*   **`components/Login.jsx`:** Renders the login form. On submission, it calls the `/api/auth/login` backend endpoint. If successful, it receives a token and user data, calls `auth.login()` to update the global state via context, and navigates the user to the main application (`/app`).
*   **`components/Signup.jsx`:** Renders the registration form. On submission, it performs basic validation (passwords match, minimum length) and calls the `/api/auth/register` backend endpoint. On success, it shows a success message and redirects to the login page.
*   **`package.json` (Client):** Lists dependencies like `react`, `react-dom`, `vite`.
    *   **Note:** It includes `bcrypt` and `jsonwebtoken`. These are typically backend dependencies. Hashing passwords and signing/verifying JWTs should happen on the server, not the client. These are likely unused or incorrectly placed in the client dependencies.

### 4.2. Backend (Server - FastAPI)

*   **`app.py`:** The heart of the backend.
    *   Initializes the FastAPI application.
    *   Configures CORS using settings from `config.py` to allow requests from the frontend.
    *   Defines Pydantic models for request/response validation (e.g., `UserLogin`, `ChatRequest`, `Token`).
    *   Sets up JWT authentication using `OAuth2PasswordBearer` and helper functions (`create_access_token`, `verify_password`, `get_password_hash`).
    *   Defines API endpoints:
        *   `/api/auth/register`: Handles user creation, hashes password, saves to MongoDB via `DataExtract`.
        *   `/api/auth/login`: Authenticates users against MongoDB data, creates and returns a JWT and user info upon success.
        *   `/api/auth/verify-token`: A protected endpoint that validates an incoming JWT and returns the associated user's data.
        *   `/api/chat`: A **protected endpoint** requiring a valid JWT. It receives a user message, uses `Depends(get_current_user)` to get the authenticated user, passes the message to `core.run_customer_support`, logs the interaction to MongoDB, and returns the AI's response along with category and sentiment.
        *   `/health`: A simple endpoint to check if the server is running.
    *   Includes logic to run the Uvicorn server for development.
*   **`core.py`:** Contains the AI logic implemented with LangChain and LangGraph.
    *   Defines the `State` TypedDict to manage the flow of data (query, category, sentiment, response).
    *   Initializes the `ChatGroq` LLM instance (**Note:** API key is hardcoded here - see Security Considerations).
    *   Defines node functions (`categorize`, `analyze_sentiment`, `handle_technical`, etc.) that use the LLM with specific prompts to perform tasks.
    *   Defines a `route_query` function to determine the next step based on sentiment and category.
    *   Builds a `StateGraph` connecting these nodes and defining the entry point and conditional edges based on `route_query`.
    *   Compiles the graph into a runnable `app`.
    *   Provides the `run_customer_support(query)` function, which is called by `app.py` to process a user message through the graph and return the final state.
*   **`components/utils.py`:**
    *   Defines the `DataExtract` class.
    *   Handles the connection to the MongoDB database (**Note:** MongoDB URI is hardcoded - see Security Considerations).
    *   Provides methods `insert_data_mongodb` and `find_one` for basic database operations needed by `app.py`. Includes basic error handling for connection and operations.
*   **`config.py`:**
    *   Loads environment variables from a `.env` file using `python-dotenv`.
    *   Retrieves the `GROQ_API_KEY`.
    *   Defines the `ALLOWED_ORIGINS` list for CORS configuration in `app.py`.
*   **`requirements.txt`:** Lists all necessary Python packages for the backend (FastAPI, LangChain, Groq, Pymongo, security libraries, etc.).

## 5. How it Works (User Flow)

1.  **Access:** User navigates to the frontend URL (e.g., `http://localhost:5173`).
2.  **Routing:** `main.jsx` checks `localStorage`. If not logged in, the user is potentially redirected to `/login`.
3.  **Signup:** If new, the user goes to `/signup`, fills the form, and submits. `Signup.jsx` sends data to `/api/auth/register`. The backend validates, hashes the password, stores the user in MongoDB, and returns success. The frontend redirects to `/login`.
4.  **Login:** User enters credentials on the `/login` page. `Login.jsx` sends data to `/api/auth/login`. The backend finds the user, verifies the password hash, generates a JWT, and returns the token + basic user info.
5.  **Authentication State:** `Login.jsx` receives the token/user info, calls `auth.login()` provided by `AuthProvider`. `AuthProvider` updates its internal state (`user`, `token`, `isAuthenticated`) and stores the token in `localStorage`.
6.  **Navigation to Chat:** The change in `isAuthenticated` state (or direct navigation after login) takes the user to the `/app` route.
7.  **Token Verification (Initial Load):** When `AuthProvider` mounts (or on refresh), it checks for a token in `localStorage`. If found, it calls `/api/auth/verify-token` to ensure the token is valid and get up-to-date user info, updating its state accordingly. If the token is invalid or missing, the user state is cleared.
8.  **Chat Interaction:**
    *   The `Chatbot` component in `App.jsx` renders.
    *   User types a message and clicks Send.
    *   `App.jsx` sends the message and the JWT (from `AuthContext`) in the `Authorization: Bearer <token>` header to the `/api/chat` endpoint.
    *   The backend's `get_current_user` dependency validates the JWT. If invalid, it returns a 401 Unauthorized error.
    *   If the token is valid, `app.py` extracts the user message and calls `core.run_customer_support(message)`.
    *   `core.py` executes the LangGraph: categorizes the query, analyzes sentiment, routes to the appropriate handler (technical, billing, general, or escalate), generates a response using Groq.
    *   `app.py` receives the result dictionary (containing response, category, sentiment) from `core.py`.
    *   `app.py` saves the user message, bot response, category, sentiment, user ID, and timestamp to the `chats` collection in MongoDB using `DataExtract`.
    *   `app.py` sends the result dictionary back to the frontend.
    *   The frontend (`App.jsx`) receives the response and updates the `messages` state, displaying the bot's reply in the chat window.
9.  **Logout:** User clicks the Logout button. `App.jsx` calls `auth.logout()`. `AuthProvider` clears its state (`user`, `token`, `isAuthenticated`) and removes the token from `localStorage`. The user is typically redirected back to `/login`.

## 6. Security Considerations

*   **Hardcoded Secrets:** **CRITICAL:** Secrets like the `SECRET_KEY` in `app.py`, `GROQ_API_KEY` in `core.py`, and `MONGODB_URI` in `utils.py` are hardcoded. This is a major security risk.
    *   **Recommendation:** Store all secrets in a `.env` file at the `server/` level. Load them *only* in `server/config.py` using `python-dotenv` and import the variables from `config.py` where needed (like in `app.py`, `core.py`, `utils.py`). **Never commit `.env` files to Git.**
*   **Client-Side Crypto:** The `client/package.json` lists `bcrypt` and `jsonwebtoken`. These should *not* be used on the client-side for hashing passwords or managing JWTs. Ensure they are removed if unused, or if used, refactor the logic to the backend.
*   **Error Handling:** While some error handling exists, ensure detailed internal errors are not exposed directly to the user in production environments. Log errors comprehensively on the server.
*   **Input Validation:** Pydantic models provide good validation on the backend. Ensure frontend inputs are also reasonably validated.
*   **Rate Limiting:** Consider adding rate limiting to API endpoints (especially auth and chat) to prevent abuse.
*   **Password Complexity:** The signup currently only checks for minimum length (6 characters). Implement stronger password complexity rules on the backend during registration.

## 7. Setup and Running Instructions

**Prerequisites:**

*   Python 3.8+ and Pip
*   Node.js and npm (or yarn)
*   Git
*   Access to a MongoDB Atlas cluster (or a local MongoDB instance)
*   A Groq API Key

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd priyanshs-ingh-customer_support_chatbot
    ```

2.  **Backend Setup (`server/`):**
    *   Navigate to the server directory:
        ```bash
        cd server
        ```
    *   **Create `.env` file:** Create a file named `.env` in the `server/` directory and add your secrets:
        ```dotenv
        # server/.env
        GROQ_API_KEY=gsk_YOUR_GROQ_API_KEY
        MONGODB_URI=mongodb+srv://<username>:<password>@<your-cluster-address>/?retryWrites=true&w=majority...
        SECRET_KEY=YOUR_VERY_STRONG_RANDOM_SECRET_KEY_FOR_JWT
        ```
        *Replace placeholders with your actual Groq key, MongoDB connection string (ensure user/password has read/write access to the `nebula` database), and generate a strong secret key (e.g., using `openssl rand -hex 64`).*
        *   **(IMPORTANT):** Modify `server/app.py`, `server/core.py`, and `server/components/utils.py` to load these secrets from `config.py` instead of using the hardcoded values.*
            *   In `config.py`, add:
                ```python
                MONGODB_URI = os.getenv('MONGODB_URI')
                SECRET_KEY = os.getenv('SECRET_KEY')
                if not MONGODB_URI: raise ValueError("MONGODB_URI not set")
                if not SECRET_KEY: raise ValueError("SECRET_KEY not set")
                ```
            *   In `app.py`, import `SECRET_KEY` from `config`.
            *   In `core.py`, import `GROQ_API_KEY` from `config` and use it when creating `ChatGroq`.
            *   In `utils.py`, import `MONGODB_URI` from `config` and use it in `connect_to_mongodb`.
    *   **Create Virtual Environment:**
        ```bash
        python -m venv venv
        ```
    *   **Activate Virtual Environment:**
        *   Windows: `.\venv\Scripts\activate`
        *   macOS/Linux: `source venv/bin/activate`
    *   **Install Python Dependencies:** Make sure you are in the `server/` directory. The `requirements.txt` is in the root, so:
        ```bash
        pip install -r ../requirements.txt
        ```
    *   **Run the Backend Server:**
        ```bash
        uvicorn app:app --reload --host 127.0.0.1 --port 8000
        ```
        The server should start on `http://127.0.0.1:8000`.

3.  **Frontend Setup (`client/`):**
    *   Open a **new terminal** or navigate back to the root and then into the client directory:
        ```bash
        cd ../client
        ```
    *   **Install Node.js Dependencies:**
        ```bash
        npm install
        # or if you use yarn:
        # yarn install
        ```
    *   **Run the Frontend Development Server:**
        ```bash
        npm run dev
        # or
        # yarn dev
        ```
        The frontend development server will likely start on `http://localhost:5173` (check the terminal output).

4.  **Access the Application:**
    *   Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
    *   You should see the Login page. Try signing up for a new account and then logging in to access the chat interface.

## 8. Further Development & Improvements

*   **Implement Admin Dashboard:** Create new components and API endpoints for admin users to monitor chats, view basic analytics (e.g., query categories, sentiment trends), and potentially manage users or canned responses.
*   **Refine AI:** Improve the prompts in `core.py` for better categorization, sentiment analysis, and response quality. Add more specific handlers if needed.
*   **Environment Variables:** Thoroughly implement the use of `.env` for *all* secrets as described in Security Considerations.
*   **Remove Client Crypto:** Clean up `client/package.json` by removing `bcrypt` and `jsonwebtoken`.
*   **Error Handling:** Enhance error handling on both frontend and backend for a smoother user experience.
*   **Testing:** Add unit tests for backend logic (especially auth and core AI functions) and potentially frontend component tests.
*   **OAuth 2.0:** If required, replace/augment the email/password flow with OAuth 2.0 provider integration (e.g., using libraries like `Authlib` on the backend).
*   **Scalability:** For higher loads, consider optimizing database queries, potentially using asynchronous database drivers (`motor` is already listed, ensure it's used effectively in `DataExtract`), and exploring serverless deployment options.
*   **Real Escalation:** Instead of just responding "escalated", implement a mechanism to actually notify a human agent (e.g., create a ticket, send an email/Slack message).
*   **Detailed Logging:** Implement more structured logging on the backend (e.g., using Python's `logging` module) to better track requests, errors, and AI interactions.
