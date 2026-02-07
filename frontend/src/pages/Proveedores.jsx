import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css';

const Proveedores = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    contactName: '',
    company: '',
    phone: '',
    rfc: '',
    address: ''
  });

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Supplier added:', formData);
    setShowModal(false);
  };

  return (
    <>
      <Navbar activeItem="Proveedores" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Proveedor"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button className="button_add" onClick={() => setShowModal(true)}>
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="Table-Wrapper">
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre del contacto</th>
                <th>Nombre</th>
                <th>Telefono</th>
                <th>RFC</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Juan Pérez</td>
                <td>Proveedor 1</td>
                <td>555-1234</td>
                <td>123456789</td>
                <ActionButtons />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Supplier Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Proveedor</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="contactName" className="form-label">Nombre del contacto</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="contactName" 
                    placeholder="Ej. Juan Pérez"
                    value={formData.contactName}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="row mb-4">
                  <div className="col-8">
                    <label htmlFor="company" className="form-label">Empresa</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="company"
                      value={formData.company}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="col-4">
                    <label htmlFor="phone" className="form-label">Telefono</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="row mb-4">
                  <div className="col-6">
                    <label htmlFor="rfc" className="form-label">RFC</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="rfc"
                      value={formData.rfc}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="col-6">
                    <label htmlFor="address" className="form-label">Dirección Fiscal</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="address"
                      value={formData.address}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="row mb-4">
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

export default Proveedores;
