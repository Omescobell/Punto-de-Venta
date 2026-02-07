import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';

const Navbar = ({ activeItem }) => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Usuarios', path: '/usuarios' },
    { name: 'Proveedores', path: '/proveedores' },
    { name: 'Ventas', path: '/ventas' },
    { name: 'Inventario', path: '/inventario' },
    { name: 'Promociones', path: '/promociones' },
    { name: 'Clientes', path: '/clientes' },
    { name: 'Métricas', path: '/metricas' }
  ];

  return (
    <header>
      <nav className="custom-navbar">
        <ul className="nav-list">
          {navItems.map((item) => (
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
