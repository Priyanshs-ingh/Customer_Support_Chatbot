import React, {
  useState,
  useRef,
  useEffect,
  useContext,
  createContext,
} from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";
import "./App.css";
import Login from "./components/Login";
import Signup from "./components/Signup";

// --- Create and EXPORT AuthContext ---
export const AuthContext = createContext({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,
  login: (newToken, userData) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("isLoggedIn", true);
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("isLoggedIn");
  },
});

// --- AuthProvider component ---
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState(() => localStorage.getItem("token"));

  // Log state changes for debugging
  useEffect(() => {
    console.log("AuthProvider: **USER STATE CHANGED** to:", user);
  }, [user]);
  useEffect(() => {
    console.log("AuthProvider: **TOKEN STATE CHANGED** to:", token);
  }, [token]);
  useEffect(() => {
    console.log("AuthProvider: **ISLOADING STATE CHANGED** to:", isLoading);
  }, [isLoading]);

  // Define login and logout methods
  const login = (newToken, userData) => {
    console.log("AuthProvider: login called.");
    try {
      localStorage.setItem("token", newToken);
      setToken(newToken);
      if (
        userData &&
        typeof userData === "object" &&
        userData.email &&
        userData.id
      ) {
        // Check essential fields
        const safeUserData = { ...userData };
        delete safeUserData.password;
        setUser(safeUserData);
        console.log("AuthProvider: User state set:", safeUserData);
      } else {
        console.error(
          "AuthProvider: Invalid/Incomplete user data received on login:",
          userData
        );
        // Set minimal user state to potentially allow isAuthenticated to pass if token exists? Risky.
        // Or better: Keep user null, which will fail !user check in ProtectedRoute
        setUser(null);
      }
    } catch (error) {
      console.error("AuthProvider: Error during login state update:", error);
    }
  };

  const logout = () => {
    console.log("AuthProvider: logout called");
    try {
      localStorage.removeItem("token");
      setToken(null);
      setUser(null);
      console.log("AuthProvider: User state cleared, token removed");
    } catch (error) {
      console.error("AuthProvider: Error during logout state update:", error);
    }
  };

  // Effect to verify token on initial mount
  useEffect(() => {
    console.log("AuthProvider Effect: Running token verification.");
    let isMounted = true;
    const verifyToken = async () => {
      if (token) {
        console.log("AuthProvider Effect: Found initial token, verifying...");
        try {
          const response = await fetch(
            "http://127.0.0.1:8000/api/auth/verify-token",
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          console.log(
            "AuthProvider Effect: Verify token API response status:",
            response.status
          );

          if (!isMounted) return;

          if (response.ok) {
            const userData = await response.json();
            if (
              userData &&
              typeof userData === "object" &&
              userData.email &&
              userData.id
            ) {
              // Check received data
              const safeUserData = { ...userData };
              delete safeUserData.password;
              setUser(safeUserData);
              console.log(
                "AuthProvider Effect: Verify token success, user state set:",
                safeUserData
              );
            } else {
              throw new Error(
                "Invalid/Incomplete user data structure from verify-token"
              );
            }
          } else {
            console.warn(
              "AuthProvider Effect: Token verification failed, status:",
              response.status,
              ". Clearing token."
            );
            localStorage.removeItem("token");
            setToken(null);
            setUser(null);
          }
        } catch (error) {
          console.error(
            "AuthProvider Effect: Error during token verification:",
            error
          );
          if (isMounted) {
            localStorage.removeItem("token");
            setToken(null);
            setUser(null);
          }
        }
      } else {
        console.log("AuthProvider Effect: No initial token found.");
        setUser(null);
      }

      if (isMounted) {
        setIsLoading(false);
      }
    };

    verifyToken();

    return () => {
      isMounted = false;
    };
  }, []); // Run only once on mount (token dependency removed to avoid loops if verify fails and clears token)

  // Construct the context value
  const authContextValue = {
    user,
    token,
    isLoading,
    login,
    logout,
    // Use the robust check combining user and token presence
    isAuthenticated: !!user && !!token,
  };

  console.log(
    "AuthProvider rendering. Providing context value:",
    authContextValue
  );

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// --- ProtectedRoute component ---
// const ProtectedRoute = ({ children }) => {
//   // Consume context including user object
//   const { isAuthenticated, isLoading, user } = useContext(AuthContext);

//   // Log exactly what ProtectedRoute sees when it renders
//   console.log(
//     `ProtectedRoute rendering: isLoading=${isLoading}, isAuthenticated=${isAuthenticated}, user=`,
//     user
//   );

//   if (isLoading) {
//     console.log("ProtectedRoute: Rendering Loading Indicator (isLoading=true)");
//     // Display a loading indicator while the initial token check is running
//     return <div className="loading">Verifying session...</div>;
//   }

//   // --- MODIFIED CHECK ---
//   // Redirect if EITHER not authenticated according to the flag OR the user object is missing.
//   // This handles the potential race condition immediately after login more leniently.
//   if (!isAuthenticated || !user) {
//     console.log(
//       `ProtectedRoute: Rendering Navigate to /login (isAuthenticated=${isAuthenticated}, userExists=${!!user})`
//     );
//     return <Navigate to="/login" replace />;
//   }
//   // --- END MODIFICATION ---

//   console.log("ProtectedRoute: Rendering children (Checks Passed)");
//   return children;
// };

// --- Chatbot component (Keep previous version with logs) ---
function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isBotLoading, setIsBotLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const { token, logout, user } = useContext(AuthContext); // Use context
  const navigate = useNavigate(); // Use navigate hook for redirection

  useEffect(() => {
    console.log("token", token);
    console.log("user", user);
    console.log(
      "Chatbot component mounted. User:",
      user,
      "Token:",
      token ? "Exists" : "null"
    );
    // Optionally add a welcome message or initial fetch here if needed
  }, [user, token]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogout = () => {
    console.log("Chatbot: handleLogout called");
    logout();
    navigate("/login", { replace: true }); // Use replace here too
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setIsBotLoading(true);

    console.log(
      "Chatbot sendMessage: Sending message:",
      userMessage,
      "with token:",
      token ? "Exists" : "null"
    );

    // Ensure token exists before sending
    if (!token) {
      console.error("Chatbot sendMessage: No token found. Logging out.");
      handleLogout();
      setIsBotLoading(false);
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // Send token
        },
        body: JSON.stringify({ message: userMessage }),
      });

      console.log("Chatbot sendMessage: API response status:", response.status);

      if (response.status === 401) {
        console.warn("Chatbot sendMessage: Unauthorized (401). Logging out.");
        handleLogout();
        return; // Stop processing
      }

      if (!response.ok) {
        let errorDetail = `Chat API error: ${response.status}`;
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || `Server error ${response.status}`;
        } catch (jsonError) {
          errorDetail = response.statusText || errorDetail;
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();
      console.log("Chatbot sendMessage: API success data:", data);

      // Check if response structure is as expected
      if (!data || typeof data.response === "undefined") {
        console.error(
          "Chatbot sendMessage: Invalid response structure from API:",
          data
        );
        throw new Error("Received invalid response from server.");
      }

      setMessages((prev) => [
        ...prev,
        {
          text: data.response, // Assuming 'response' key exists
          category: data.category,
          sentiment: data.sentiment,
          isUser: false,
        },
      ]);
    } catch (error) {
      console.error("Chatbot sendMessage: Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          text: `Error: ${error.message}. Please try again.`,
          isUser: false,
          isError: true,
        },
      ]);
      // Optional: Check if the error indicates an invalid token even if not 401
      if (
        error.message &&
        (error.message.toLowerCase().includes("validate credentials") ||
          error.message.toLowerCase().includes("token"))
      ) {
        console.warn(
          "Chatbot sendMessage: Error suggests token issue. Logging out."
        );
        handleLogout();
      }
    } finally {
      setIsBotLoading(false);
    }
  };

  return (
    <div className="chatbot-main">
      <div className="chatbot-header">
        <h2>Customer Support</h2>
        {user && <span className="user-email">Logged in as: {user.email}</span>}
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
      <div className="messages-container">
        {messages.length === 0 && !isBotLoading && (
          <div className="welcome-message">
            <p>👋 Hi {user?.email || "there"}! How can I help you today?</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message-wrapper ${message.isUser ? "user" : "bot"} ${
              message.isError ? "error" : ""
            }`}
          >
            <div className="message">
              <span className="message-icon">
                {message.isUser ? "👤" : message.isError ? "⚠️" : "🤖"}
              </span>
              <div className="message-content">{message.text}</div>
              {!message.isUser && message.category && (
                <div className="message-meta">Category: {message.category}</div>
              )}
              {!message.isUser && message.sentiment && (
                <div className="message-meta">
                  Sentiment: {message.sentiment}
                </div>
              )}
            </div>
          </div>
        ))}
        {isBotLoading && (
          <div className="message-wrapper bot">
            <div className="message">
              <span className="message-icon">🤖</span>
              <div className="message-content typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={sendMessage} className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="message-input"
          disabled={isBotLoading}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isBotLoading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
}

// --- Main App component ---
function App() {
  console.log("App component rendering. Setting up AuthProvider and Router.");
  return (
    <Chatbot />
    // <AuthProvider>
    // <Router>
    //   <Routes>
    //     <Route path="/login" element={<Login />} />
    //     <Route path="/signup" element={<Signup />} />
    //     <Route
    //       path="/chat"
    //       element={
    //         // <ProtectedRoute>

    //         // </ProtectedRoute>
    //       }
    //     />
    //     <Route path="*" element={<Navigate to="/" replace />} />
    //   </Routes>
    // </Router>
    // </AuthProvider>
  );
}

export default App;
