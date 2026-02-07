import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css';

const Usuarios = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    address: '',
    userLevel: '',
    phone: ''
  });

  const subHeaderItems = [
    { name: 'Usuarios', path: '/usuarios' },
    { name: 'ChatBot', path: '/chatbot' }
  ];

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form submitted:', formData);
    setShowModal(false);
  };

  return (
    <>
      <Navbar activeItem="Usuarios" />
      <SubHeader items={subHeaderItems} activeItem="Usuarios" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Usuario"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button 
            className="button_add" 
            onClick={() => setShowModal(true)}
          >
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="Table-Wrapper">
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre Completo</th>
                <th>Telefono</th>
                <th>Dirección</th>
                <th>Nivel de <br />Usuario</th>
                <th style={{ width: '200px' }}></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Juan Pérez</td>
                <td>555-1234</td>
                <td>Calle Falsa 123</td>
                <td>Admin</td>
                <ActionButtons 
                  onEdit={() => console.log('Edit')} 
                  onDelete={() => console.log('Delete')} 
                />
              </tr>
              {/* Only show action buttons when there's real data */}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Usuario</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="row mb-4">
                  <label htmlFor="name" className="form-label">Nombre Completo</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="name" 
                    placeholder="Ej. Juan Pérez"
                    value={formData.name}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="row mb-4">
                  <label htmlFor="email" className="form-label">Correo Electrónico</label>
                  <input 
                    type="email" 
                    className="form-control" 
                    id="email" 
                    placeholder="correo@ejemplo.com"
                    value={formData.email}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="row mb-4">
                  <label htmlFor="address" className="form-label">Dirección</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="address"
                    placeholder="Ej. Calle 123"
                    value={formData.address}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="row mb-4">
                  <div className="col-6">
                    <label className="form-label">Nivel de Usuario</label>
                    <select 
                      className="form-select"
                      id="userLevel"
                      value={formData.userLevel}
                      onChange={handleInputChange}
                    >
                      <option value="">Seleccionar...</option>
                      <option value="1">Dueño</option>
                      <option value="2">Administrador</option>
                      <option value="3">Empleado</option>
                    </select>
                  </div>
                  <div className="col-6">
                    <label htmlFor="phone" className="form-label">Teléfono</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                <div className="mb-3">
                  <button type="submit" className="btn btn-primary">Guardar Usuario</button>
                </div>
              </form>
            </div>
          </div>
        </div>
        {showModal && <div className="modal-backdrop fade show" onClick={() => setShowModal(false)}></div>}
      </div>
    </>
  );
};

export default Usuarios;
