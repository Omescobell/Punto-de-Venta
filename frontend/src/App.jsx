import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Login from './pages/Login';
import Usuarios from './pages/Usuarios';
import Clientes from './pages/Clientes';
import Ventas from './pages/Ventas';
import Inventario from './pages/Inventario';
import Promociones from './pages/Promociones';
import Proveedores from './pages/Proveedores';
import Metricas from './pages/Metricas';
import MetricasProductos from './pages/MetricasProductos';
import Chatbot from './pages/Chatbot';

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes wrapped in MainLayout */}
        <Route element={<MainLayout />}>
          <Route path="/usuarios" element={<Usuarios />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/ventas" element={<Ventas />} />
          <Route path="/inventario" element={<Inventario />} />
          <Route path="/promociones" element={<Promociones />} />
          <Route path="/proveedores" element={<Proveedores />} />
          <Route path="/metricas" element={<Metricas />} />
          <Route path="/metricas-productos" element={<MetricasProductos />} />
          <Route path="/chatbot" element={<Chatbot />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
