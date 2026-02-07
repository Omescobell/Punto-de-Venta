import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Clientes.css';

const Clientes = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <Navbar activeItem="Clientes" />
      
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
                <th>Nombre</th>
                <th>Telefono</th>
                <th>Cumpleaños</th>
                <th>Correo</th>
                <th style={{ width: '200px' }}></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Juan Pérez</td>
                <td>33122298</td>
                <td>01/01/2000</td>
                <td>juanperez@gmail.com</td>
                <ActionButtons />
              </tr>
              <tr>
                <td>María López</td>
                <td>555-5678</td>
                <td>01/01/2000</td>
                <td>marialopez@gmail.com</td>
                <ActionButtons />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Client Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body p-0">
              <h2 className="text-center mb-5">Agregar Cliente</h2>
              
              <form>
                <div className="row mb-4">
                  <label className="form-label">Nombre</label>
                  <input type="text" className="form-control" placeholder="Value" />
                </div>

                <div className="row mb-4">
                  <div className="col-md-6">
                    <label className="form-label">Fecha de cumpleaños</label>
                    <div className="d-flex gap-2">
                      <input type="text" className="form-control text-center" placeholder="DD" />
                      <input type="text" className="form-control text-center" placeholder="MM" />
                    </div>
                  </div>
                  
                  <div className="col-md-6">
                    <label className="form-label">Teléfono</label>
                    <input type="text" className="form-control" placeholder="Value" />
                  </div>
                </div>

                <div className="row mb-4">
                  <label className="form-label">Correo electrónico</label>
                  <input type="email" className="form-control" placeholder="Value" />
                </div>

                <div className="d-grid mt-4">
                  <button type="submit" className="btn btn-dark-custom">Agregar Promoción</button>
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

export default Clientes;
