import { Link, useLocation, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useState, useEffect } from 'react';

const Navbar = ({ activeItem }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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
    }

    // Si el item permite el rol actual, mostrarlo
    return item.roles.includes(normalizedRole);
  });

  const userType = () => {
    if(userRole === 'OWNER') return 'Dueño';
    if(userRole === 'ADMIN') return 'Administrador';
    if(userRole === 'EMPLOYEE') return 'Empleado';
    return '';
  };

  return (
    <header className="w-full bg-white shadow-sm font-sans relative z-40 mb-6">
      {/* Top Bar: User Info & Logout */}
      <div className="flex flex-row justify-between items-center px-4 md:px-8 py-3 bg-[#f8f9fa] border-b border-gray-200">
        <div className="flex items-center gap-3">
          {userType() && (
            <span className="bg-blue-100 text-blue-800 text-xs md:text-sm font-bold px-3 py-1 rounded-full border border-blue-200 tracking-wide uppercase">
              {userType()}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <h4 className="hidden md:block m-0 text-gray-600 font-medium text-sm">Cerrar Sesión</h4>
          <button 
            className="text-gray-600 hover:text-red-500 transition-colors p-2 rounded-full hover:bg-red-50 flex items-center justify-center"
            onClick={handleLogout} 
            aria-label="Cerrar sesión"
          >
            <i className="bi bi-box-arrow-right text-xl md:text-2xl"></i>
          </button>
        </div>
      </div>

      {/* Navigation Bar */}
      <nav className="px-4 md:px-8 py-3 md:py-4 bg-white transition-all duration-300">
        <div className="flex justify-between items-center lg:hidden">
            <span className="text-lg font-bold text-gray-800 tracking-tight">Menú Principal</span>
            {/* Hamburger Button */}
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-600 focus:outline-none p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <i className={`bi ${isMenuOpen ? 'bi-x-lg' : 'bi-list'} text-3xl leading-none`}></i>
            </button>
        </div>

        {/* Links List */}
        <div className={`${isMenuOpen ? 'block' : 'hidden'} lg:block w-full mt-4 lg:mt-0`}>
          <ul className="flex flex-col lg:flex-row lg:flex-wrap lg:justify-center items-center gap-2 lg:gap-6 p-0 m-0 list-none w-full">
            {visibleItems.map((item) => {
              const isActive = location.pathname === item.path || activeItem === item.name;
              return (
                <li key={item.path} className="w-full lg:w-auto text-center">
                  <Link 
                    to={item.path}
                    onClick={() => setIsMenuOpen(false)}
                    className={`block lg:inline-block px-4 py-3 lg:py-2 lg:px-6 rounded-lg text-[18px] lg:text-[22px] font-medium transition-all duration-300 w-full lg:w-auto ${
                      isActive 
                        ? 'bg-gray-200 text-gray-900 shadow-inner' 
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>
      </nav>
    </header>
  );
};

Navbar.propTypes = {
  activeItem: PropTypes.string
};

export default Navbar;
