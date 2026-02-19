import { Link, useLocation, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useState, useEffect } from 'react';

const Navbar = ({ activeItem }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState('');
  
  useEffect(() => {
    const role = localStorage.getItem('role');
    if (role) {
      setUserRole(role);
    }
  }, []);

  const handleLogout = async () => {
    const id = localStorage.getItem('user_id');
    const token = localStorage.getItem('access_token');
    
    // Intentar revocar sesión en backend primero
    if (id && token) {
      try {
        await fetch(`/api/sessions/${id}/revoke/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error("Error closing session:", error);
      }
    }

    // Limpiar storage local
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user'); // Legacy
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('user_id');
    
    navigate('/login');
  };
  
  //* Definición de todos los items de navegación con sus permisos requeridos
  const allNavItems = [
    { name: 'Usuarios', path: '/usuarios', roles: ['ADMIN', 'OWNER'] },
    { name: 'Proveedores', path: '/proveedores', roles: ['ADMIN', 'OWNER'] },
    { name: 'Ventas', path: '/ventas', roles: ['ADMIN', 'OWNER', 'EMPLOYEE'] },
    { name: 'Inventario', path: '/inventario', roles: ['ADMIN', 'OWNER', 'EMPLOYEE'] },
    { name: 'Promociones', path: '/promociones', roles: ['ADMIN', 'OWNER'] },
    { name: 'Clientes', path: '/clientes', roles: ['ADMIN', 'OWNER', 'EMPLOYEE'] },
    { name: 'Métricas', path: '/metricas', roles: ['ADMIN', 'OWNER'] }
  ];

  // Normalizar rol para comparación
  const normalizedRole = userRole ? userRole.toUpperCase() : '';

  // Filtrar items basado en el rol
  const visibleItems = allNavItems.filter(item => {
    // Si no hay rol (no logueado), no mostrar nada
    if (!normalizedRole){
      return false;
      navigate('/login');
    };

    // Si el item permite el rol actual, mostrarlo
    return item.roles.includes(normalizedRole);
  });

  return (
    <header className={`header-container ${normalizedRole.toLowerCase()}-theme`}>
      <div className="Superior">
        <div className="user-info-display">
            {/* Opcional: Mostrar rol o usuario */}
            <span className="role-badge">{userRole}</span>
        </div>
        <div className="logout-section">
            <h4>Cerrar Sesión</h4>
            <button className="button_logout" onClick={handleLogout} aria-label="Cerrar sesión">
            <i className="bi bi-box-arrow-right"></i>
            </button>
        </div>
      </div>
      <nav className={`custom-navbar ${normalizedRole.toLowerCase()}-nav`}>
        <ul className="nav-list">
          {visibleItems.map((item) => (
            <li 
              key={item.path} 
              className={`nav-item ${location.pathname === item.path || activeItem === item.name ? 'active' : ''}`}
            >
              <Link to={item.path}>{item.name}</Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
};

Navbar.propTypes = {
  activeItem: PropTypes.string
};

export default Navbar;
