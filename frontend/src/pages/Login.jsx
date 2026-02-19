import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';

const Login = () => {
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const targetUrl = '/api/auth/login/';
      console.log('Attempting login with:', { email: credentials.email, url: targetUrl });
      
      const requestHeaders = new Headers();
      requestHeaders.append('Content-Type', 'application/json');

      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify(credentials),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        
        // Fetch user details
        try {
          const userResponse = await fetch('/api/users/me/', {
            headers: {
              'Authorization': `Bearer ${data.access}`
            }
          });
          
          if (userResponse.ok) {
            const userData = await userResponse.json();
            localStorage.setItem('username', userData.username);
            localStorage.setItem('role', userData.role);
            localStorage.setItem('user_id', userData.id);
            console.log('Login successful, user details loaded:', userData);
          } else {
            console.warn('Could not fetch user details. Status:', userResponse.status);
          }
        } catch (userErr) {
          console.error('Error fetching user details:', userErr);
        }

        // Redirect to sales page or dashboard
        navigate('/ventas');
      } else {
        console.error('Login failed with status:', response.status, data);
        setError(data.detail || `Error (${response.status}): ${JSON.stringify(data)}`);
      }
    } catch (err) {
      console.error('Login network error:', err);
      setError(`Error de conexión: ${err.message}. Revise la consola para más detalles.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="Container"> {/* Changed from login-container to Container based on CSS class name in file */}
        <div className="login-box">
          <h1>Punto de Venta</h1>
          <h2>Iniciar Sesión</h2>
          {error && <div className="alert alert-danger" role="alert">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="mb-3 lft">
              <label htmlFor="email" className="form-label">Correo Electrónico</label>
              <input 
                type="email"
                className="form-control" 
                id="email"
                value={credentials.email}
                onChange={(e) => setCredentials({...credentials, email: e.target.value})}
              />
            </div>
            <div className="mb-3 lft">
              <label htmlFor="password" className="form-label">Contraseña</label>
              <input 
                type="password" 
                className="form-control" 
                id="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              />
            </div>
            <button type="submit" className="btn btn-primary w-100" disabled={loading}>
              {loading ? 'Cargando...' : 'Entrar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
