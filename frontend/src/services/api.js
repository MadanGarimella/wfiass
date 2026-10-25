const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export const getHealth = () => request("/health");
export const getMetadata = () => request("/metadata");
export const getSummary = () => request("/summary");
export const getForecasts = () => request("/forecasts");
export const getDailyForecasts = () => request("/forecasts/daily");
export const getAnalysis = () => request("/analysis");
