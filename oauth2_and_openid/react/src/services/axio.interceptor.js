import axios from "axios";
import keycloakInstance from "./keycloakService";

const api = axios.create({
  timeout: 10000,
});

api.interceptors.request.use(
  (config) => {
    if (keycloakInstance.token) {
      config.headers.Authorization = `Bearer ${keycloakInstance.token}`;
    }

    return config;
  },
  (error) => {
    toast.error("Error doing request. Code: ", error)
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        console.error("No autorizado. Redirigir al login...");
      }
    }
    return Promise.reject(error);
  }
);
export default api;
