import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

// Attach bearer as fallback (in case cookies blocked in preview)
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("sz_access_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export function setToken(t) {
  if (t) localStorage.setItem("sz_access_token", t);
  else localStorage.removeItem("sz_access_token");
}

export function apiErr(e) {
  const d = e?.response?.data?.detail;
  if (!d) return e?.message || "Something went wrong";
  if (typeof d === "string") return d;
  if (Array.isArray(d))
    return d.map((x) => (x?.msg ? x.msg : JSON.stringify(x))).join(" ");
  return String(d);
}

export default api;
