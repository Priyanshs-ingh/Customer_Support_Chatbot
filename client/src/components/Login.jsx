import React, { useState, useContext, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../App"; // Ensure this path is correct
import "./Login.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isApiLoading, setIsApiLoading] = useState(false); // Local loading state for API call
  const [loginAttemptComplete, setLoginAttemptComplete] = useState(false); // State to trigger navigation
  const navigate = useNavigate();
  const auth = useContext(AuthContext); // Consume context

  // // Log context changes (optional, keep for debugging if needed)
  // useEffect(() => {
  //   console.log("Login component received auth context:", auth);
  //   if (auth) {
  //     console.log("Login component: auth.isLoading:", auth.isLoading);
  //   }
  // }, [auth]);

  // // --- Effect to Navigate AFTER State Update ---
  // useEffect(() => {
  //   // Only navigate if the login attempt was successful
  //   if (auth.isAuthenticated === true) {
  //     console.log("auth", auth);
  //     console.log(
  //       "Login.jsx Effect: loginAttemptComplete is true, navigating to '/'"
  //     );
  //     // Use replace to prevent user from going back to the login page via back button
  //     navigate("/app", { replace: true });
  //   }
  // }, [auth, auth.isAuthenticated, navigate]); // Depend on the state variable and navigate function

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsApiLoading(true); // Start API call loading indicator
    setLoginAttemptComplete(false); // Reset navigation trigger

    console.log("HandleLogin triggered. Checking auth context:", auth);

    if (!auth || typeof auth.login !== "function") {
      setError("Authentication system failed to initialize.");
      console.error(
        "CRITICAL: Auth context still missing or invalid in handleLogin:",
        auth
      );
      setIsApiLoading(false);
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        let errorDetail = `Login failed: ${response.status}`;
        try {
          const errorData = await response.json();
          // Prefer backend detail message if available
          errorDetail =
            errorData.detail ||
            `Login failed: ${response.status} ${response.statusText}`;
        } catch (jsonError) {
          errorDetail = response.statusText
            ? `Login failed: ${response.status} ${response.statusText}`
            : errorDetail;
        }
        console.error("Login API Error:", errorDetail);
        setError(
          errorDetail.startsWith("Incorrect")
            ? errorDetail
            : "Login failed. Please check credentials or try again."
        );
        setIsApiLoading(false); // Stop loading on error
        return; // Important: Stop execution on error
      }

      // --- SUCCESS ---
      const data = await response.json();
      console.log("Login successful, API data:", data);
      console.log("Login.jsx: Calling auth.login()...");
      auth.login(data.token, data.user); // Call login from context to update state
      console.log("Login.jsx: Setting loginAttemptComplete to true.");
      // setLoginAttemptComplete(true); // Set state to trigger navigation EFFECT
      auth.user = data.user; // Update context state directly
      auth.token = data.token; // Update context state directly
      auth.isAuthenticated = true; // Update context state directly
      console.log("Login.jsx: auth.isAuthenticated set to true.", auth);
      navigate("/app", { replace: true }); // Navigate to home page
    } catch (error) {
      console.error("Login Fetch/Network Error:", error);
      setError("An error occurred connecting to the server. Please try again.");
      setIsApiLoading(false); // Stop loading on catch
    }
    // No need to set isApiLoading false on success path here, as we navigate away
  };

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Login to Customer Support</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={isApiLoading} // Disable inputs during API call
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={isApiLoading} // Disable inputs during API call
            />
          </div>
          <button
            type="submit"
            className="auth-button"
            disabled={isApiLoading} // Disable button only during API call
          >
            {isApiLoading ? "Logging in..." : "Login"}
          </button>
        </form>
        <p className="auth-redirect">
          Don't have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
