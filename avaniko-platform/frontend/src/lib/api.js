import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "https://api.avaniko.com";

// ── Axios instance for Dashboard (JWT auth) ──────────────
export const dashApi = axios.create({ baseURL: BASE_URL });

dashApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

dashApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────
export const authAPI = {
  signup: (data) => dashApi.post("/auth/signup", data),
  login:  (data) => dashApi.post("/auth/login", data),
  me:     ()     => dashApi.get("/auth/me"),
};

// ── API Keys ─────────────────────────────────────────────
export const keysAPI = {
  list:   ()          => dashApi.get("/v1/api-keys"),
  create: (data)      => dashApi.post("/v1/api-keys/create", data),
  revoke: (keyId)     => dashApi.delete(`/v1/api-keys/${keyId}`),
};

// ── Usage ────────────────────────────────────────────────
export const usageAPI = {
  get: (apiKey, days = 30) =>
    axios.get(`${BASE_URL}/v1/usage?days=${days}`, {
      headers: { "x-api-key": apiKey }
    }),
};

// ── Projects ─────────────────────────────────────────────
export const projectsAPI = {
  list:   (apiKey)           => axios.get(`${BASE_URL}/v1/projects`,               { headers: { "x-api-key": apiKey } }),
  create: (apiKey, data)     => axios.post(`${BASE_URL}/v1/projects`, data,         { headers: { "x-api-key": apiKey } }),
  update: (apiKey, id, data) => axios.put(`${BASE_URL}/v1/projects/${id}`, data,   { headers: { "x-api-key": apiKey } }),
  delete: (apiKey, id)       => axios.delete(`${BASE_URL}/v1/projects/${id}`,      { headers: { "x-api-key": apiKey } }),
};

// ── Models ───────────────────────────────────────────────
export const modelsAPI = {
  list: (apiKey) => axios.get(`${BASE_URL}/v1/models`, { headers: { "x-api-key": apiKey } }),
};

// ── Chat streaming helper ─────────────────────────────────
export async function* streamChat({ apiKey, messages, model, system, projectId }) {
  const res = await fetch(`${BASE_URL}/v1/chat/completions`, {
    method:  "POST",
    headers: { "x-api-key": apiKey, "Content-Type": "application/json" },
    body:    JSON.stringify({
      model, messages, stream: true,
      ...(system     && { system }),
      ...(projectId  && { project_id: projectId })
    })
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);

  const reader  = res.body.getReader();
  const decoder = new TextDecoder();
  let   buffer  = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const dataStr = line.slice(5).trim();
      if (dataStr === "[DONE]") return;
      try {
        const data  = JSON.parse(dataStr);
        const token = data.choices?.[0]?.delta?.content;
        if (token) yield token;
      } catch {}
    }
  }
}
