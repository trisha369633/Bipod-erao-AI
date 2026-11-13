const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

async function postAnalysis(path, payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    throw error;
  }

  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      response.ok ? "ANALYSIS_RESPONSE_INVALID" : "ANALYSIS_SERVICE_UNAVAILABLE",
    );
  }

  if (!response.ok) {
    if (response.status === 404 || response.status >= 500) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    throw new Error(
      typeof data?.detail === "string" || typeof data?.error === "string"
        ? data.detail ?? data.error
        : "ANALYSIS_SERVICE_UNAVAILABLE",
    );
  }

  if (
    !data ||
    !Array.isArray(data.urls) ||
    typeof data.live_reputation_available !== "boolean"
  ) {
    throw new Error("ANALYSIS_RESPONSE_INVALID");
  }
  return data;
}

async function postDualAnalysis(path, payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    throw error;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      response.ok ? "ANALYSIS_RESPONSE_INVALID" : "ANALYSIS_SERVICE_UNAVAILABLE",
    );
  }

  if (!response.ok) {
    if (
      response.status === 503 &&
      data?.detail?.code === "GEMINI_UNAVAILABLE"
    ) {
      const error = new Error(
        typeof data.detail.message === "string"
          ? data.detail.message
          : "GEMINI_UNAVAILABLE",
      );
      error.code = "GEMINI_UNAVAILABLE";
      throw error;
    }
    if (response.status === 404 || response.status >= 500) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    const error = new Error(data?.detail ?? "DUAL_ANALYSIS_FAILED");
    error.code =
      response.status === 422 ? "INVALID_ANALYSIS_INPUT" : "DUAL_ANALYSIS_FAILED";
    throw error;
  }

  if (
    !data ||
    !["phishing", "legitimate"].includes(data.final_decision?.prediction) ||
    typeof data.decision_explanation !== "string"
  ) {
    throw new Error("ANALYSIS_RESPONSE_INVALID");
  }
  return data;
}

export async function analyzeMessage(message) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/message-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    throw error;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      response.ok ? "ANALYSIS_RESPONSE_INVALID" : "ANALYSIS_SERVICE_UNAVAILABLE",
    );
  }

  if (!response.ok) {
    if (response.status === 404 || response.status >= 500) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    const error = new Error(data?.detail ?? "MESSAGE_ANALYSIS_FAILED");
    error.code = response.status === 422 ? "INVALID_MESSAGE" : "MESSAGE_ANALYSIS_FAILED";
    throw error;
  }

  return data;
}

export function analyzeDualMessage(message, language) {
  return postDualAnalysis("/api/dual/message-check", { message, language });
}

export function analyzeMessageUrls(message) {
  return postAnalysis("/api/url-analysis", { message });
}

export function analyzeDualUrl(url, language) {
  return postDualAnalysis("/api/dual/url-check", { url, language });
}

export async function analyzeLink(url) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/url-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    throw error;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      response.ok ? "ANALYSIS_RESPONSE_INVALID" : "ANALYSIS_SERVICE_UNAVAILABLE",
    );
  }

  if (!response.ok) {
    if (response.status === 404 || response.status >= 500) {
      throw new Error("ANALYSIS_SERVICE_UNAVAILABLE");
    }
    const error = new Error(
      typeof data?.detail === "string" ? data.detail : "URL_ANALYSIS_FAILED",
    );
    error.code = response.status === 422 ? "INVALID_URL" : "URL_ANALYSIS_FAILED";
    throw error;
  }

  if (
    !data ||
    typeof data.url !== "string" ||
    !["phishing", "legitimate"].includes(data.prediction) ||
    !["high", "low"].includes(data.risk_level) ||
    typeof data.model_confidence !== "number" ||
    !Number.isFinite(data.model_confidence) ||
    data.model_confidence < 0 ||
    data.model_confidence > 1 ||
    typeof data.message !== "string"
  ) {
    throw new Error("ANALYSIS_RESPONSE_INVALID");
  }
  return data;
}