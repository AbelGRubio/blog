import { useState, useEffect } from 'react'
import './App.css'
import keycloakInstance, { initKeycloak, handleLogout } from "./services/keycloakService";
import api from './services/axio.interceptor';

async function fetchProtectedResource() {
  try {
    const response = await api.get("http://localhost:8000/protected");
    console.log("Data protected:", response.data);
    return response;
  } catch (error) {
    console.error("Error:", error);
    return 'Error';
  }
}

function App() {
  const [response, setResponse] = useState("press the button")
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const authenticate = async () => {
      const isAuthenticated = await initKeycloak();
      console.log("------");
      console.log(isAuthenticated);
      setInitialized(isAuthenticated);
    };

    authenticate();
  }, []);

  if (!initialized) {
    return <div>Loading...</div>;
  }
  
    return keycloakInstance && keycloakInstance.authenticated ? (
    <>
      <h1>You are logged</h1>
      <div className="card">
        <button onClick={async () =>  {
          const response = await fetchProtectedResource();
          console.log(response);
          setResponse(response?.data.message ?? 'Error');
        }}>
          Press this botton 
        </button>
        <p style={{ marginTop: '1rem' }}>        The response is: {response}
</p>
      </div>

    </>
  ) : (
    <div>No authenticated</div>
  );
}

export default App
