import axios from "axios";

const baseURL = process.env.REACT_APP_API_URL || "http://localhost:5000";

const client = axios.create({
  baseURL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiErrorMessage(error, fallback = "Something went wrong.") {
  if (!error) return fallback;
  if (error.response?.data?.message) return error.response.data.message;
  if (error.message === "Network Error") {
    return "Cannot reach the backend API. Is Flask running on port 5000?";
  }
  if (error.code === "ECONNABORTED") {
    return "Request timed out. The analysis pipeline may still be running.";
  }
  return error.message || fallback;
}

export default client;
