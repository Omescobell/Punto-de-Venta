import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css';
import '../styles/General.css';

const Chatbot = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    employee: '',
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
    console.log('ChatBot user added:', formData);
    setShowModal(false);
  };

  return (
    <>
      <Navbar activeItem="Usuarios" />
      <SubHeader items={subHeaderItems} activeItem="ChatBot" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Usuario"
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
                <th>Nombre Completo</th>
                <th>Telefono</th>
                <th style={{ width: '200px' }}></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Juan Pérez</td>
                <td>33122298</td>
                <ActionButtons />
              </tr>
              <tr>
                <td>María López</td>
                <td>555-5678</td>
                <ActionButtons />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Add ChatBot User Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Usuario</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="row mb-4">
                  <div>
                    <label className="form-label">Nombre del empleado</label>
                    <select 
                      className="form-select"
                      id="employee"
                      value={formData.employee}
                      onChange={handleInputChange}
                    >
                      <option value="">Seleccionar...</option>
                      <option value="1">Ernesto Perez</option>
                      <option value="2">Oscar Sanchez</option>
                      <option value="3">Juan Perez</option>
                    </select>
                  </div>
                </div>
                
                <div className="row mb-3">
                  <label className="form-label">Telefono vinculado</label>
                  <input 
                    type="number" 
                    className="form-control"
                    id="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                  />
                </div>
                
                <div className="row mb-3">
                  <button type="submit" className="btn btn-primary">Agregar a ChatBot</button>
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

export default Chatbot;
