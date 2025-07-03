import Keycloak from "keycloak-js";


const keycloakOptions = {
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_REALM, 
  clientId: import.meta.env.VITE_CLIENT_ID, 
};

const keycloakInstance = new Keycloak(keycloakOptions);
let authenticated = null;
/**
 * Initializes Keycloak and handles authentication.
 * @param {Function} setUser - Function to set the user information.
 * @param {Function} addItem - Function to add allowed routes to the store.
 * @param {Function} setConfig - Function to set the backend configuration.
 */
export const initKeycloak = async () => {
  try {
    if (!authenticated){
      authenticated = await keycloakInstance.init({
        onLoad: "login-required", 
        checkLoginIframe: false,
      });
    }

    if (authenticated) {

      setInterval(async () => {
        if (keycloakInstance.isTokenExpired()) {
          await keycloakInstance.updateToken(30);
        }
      }, 30000);

    }

    return authenticated;
  } catch (error) {
    console.error(`Error in Keycloak: ${error}`);
    return false;
  }
};

/**
 * Close and clean the session.
 */
export const handleLogout = () => {
  if (keycloakInstance) {
    sessionStorage.removeItem("token");
    keycloakInstance.logout();
  }
};

export default keycloakInstance;