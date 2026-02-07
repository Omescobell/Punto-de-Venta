import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Promociones.css';

const Promociones = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBirthdayModal, setShowBirthdayModal] = useState(false);

  // State for Add Promotion Form
  const [promoData, setPromoData] = useState({
    name: '',
    description: '',
    accessLevel: '',
    discount: '',
    activeDay: '',
    activeMonth: '',
    activeYear: '',
    product: ''
  });

  // State for Birthday Config Form
  const [birthdayData, setBirthdayData] = useState({
    type: '',
    minSpend: '',
    discount: ''
  });

  const handlePromoChange = (e) => {
    const { id, value } = e.target;
    setPromoData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleBirthdayChange = (e) => {
    const { id, value } = e.target;
    setBirthdayData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handlePromoSubmit = (e) => {
    e.preventDefault();
    console.log('Promotion Data:', promoData);
    setShowAddModal(false);
  };

  const handleBirthdaySubmit = (e) => {
    e.preventDefault();
    console.log('Birthday Config:', birthdayData);
    setShowBirthdayModal(false);
  };

  return (
    <>
      <Navbar activeItem="Promociones" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Promoción"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="d-flex gap-3">
            <button className="button_add wide" onClick={() => setShowAddModal(true)}>
              Agregar Promoción
              <i className="bi bi-plus-lg"></i>
            </button>
            <button className="button_replay" onClick={() => setShowBirthdayModal(true)}>
              <i className="bi bi-arrow-counterclockwise"></i>
            </button>
          </div>
        </div>

        <div className="Table-Wrapper">
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Descuento</th>
                <th>Productos</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>01/01/2024 - 31/01/2024</td>
                <td>10%</td>
                <td>Producto A, Producto B</td>
                <ActionButtons 
                  onEdit={() => console.log('Edit')} 
                  onDelete={() => console.log('Delete')} 
                />
              </tr>
              {/* Only show rows with data */}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Promotion Modal */}
      <div className={`modal fade ${showAddModal ? 'show' : ''}`} 
           style={{ display: showAddModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Promoción</h2>
              
              <form onSubmit={handlePromoSubmit}>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="name" className="form-label">Nombre</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="name"
                      value={promoData.name}
                      onChange={handlePromoChange}
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="description" className="form-label">Descripción</label>
                    <textarea 
                      className="form-control" 
                      id="description"
                      value={promoData.description}
                      onChange={handlePromoChange}
                      rows="1"
                    ></textarea>
                  </div>
                </div>

                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="accessLevel" className="form-label">Clientes</label>
                    <select 
                      className="form-select" 
                      id="accessLevel"
                      value={promoData.accessLevel}
                      onChange={handlePromoChange}
                    >
                      <option value="">Seleccionar...</option>
                      <option value="all">Todos</option>
                      <option value="vip">Premium</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="discount" className="form-label">Descuento (%)</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="discount"
                      value={promoData.discount}
                      onChange={handlePromoChange}
                    />
                  </div>
                </div>

                <div className="row mb-4">
                  <div className="col-md-6">
                    <label className="form-label">Activo hasta</label>
                    <div className="d-flex gap-2">
                       <input 
                        type="text" 
                        className="form-control text-center" 
                        placeholder="DD" 
                        id="activeDay"
                        style={{ width: '60px' }}
                        value={promoData.activeDay}
                        onChange={handlePromoChange}
                      />
                      <input 
                        type="text" 
                        className="form-control text-center" 
                        placeholder="MM" 
                        id="activeMonth"
                        style={{ width: '60px' }}
                        value={promoData.activeMonth}
                        onChange={handlePromoChange}
                      />
                      <input 
                        type="text" 
                        className="form-control text-center" 
                        placeholder="AAAA" 
                        id="activeYear"
                        style={{ width: '80px' }}
                        value={promoData.activeYear}
                        onChange={handlePromoChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="product" className="form-label">Producto</label>
                    <select 
                      className="form-select" 
                      id="product"
                      value={promoData.product}
                      onChange={handlePromoChange}
                    >
                      <option value="">Seleccionar...</option>
                      <option value="1">Producto A</option>
                      <option value="2">Producto B</option>
                    </select>
                  </div>
                </div>

                <div className="mb-3">
                  <button type="submit" className="button_Modal">Agregar</button>
                </div>
              </form>
            </div>
          </div>
        </div>
        {showAddModal && <div className="modal-backdrop fade show" onClick={() => setShowAddModal(false)}></div>}
      </div>

      {/* Birthday Config Modal */}
      <div className={`modal fade ${showBirthdayModal ? 'show' : ''}`} 
           style={{ display: showBirthdayModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Configurar Cumpleaños</h2>
              
              <form onSubmit={handleBirthdaySubmit}>
                <div className="row mb-4">
                  <label htmlFor="type" className="form-label">Tipo de recompensa</label>
                  <select 
                    className="form-select" 
                    id="type"
                    value={birthdayData.type}
                    onChange={handleBirthdayChange}
                  >
                    <option value="">Seleccionar...</option>
                    <option value="discount">Descuento</option>
                    <option value="gift">Regalo</option>
                  </select>
                </div>

                <div className="row mb-4">
                  <div className="col-md-6">
                    <label htmlFor="minSpend" className="form-label">Compra Mínima</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="minSpend"
                      value={birthdayData.minSpend}
                      onChange={handleBirthdayChange}
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="discount" className="form-label">Descuento</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="discount"
                      value={birthdayData.discount}
                      onChange={handleBirthdayChange}
                    />
                  </div>
                </div>

                <div className="row mb-3">
                  <button type="submit" className="button_Modal">Guardar Configuración</button>
                </div>
              </form>
            </div>
          </div>
        </div>
        {showBirthdayModal && <div className="modal-backdrop fade show" onClick={() => setShowBirthdayModal(false)}></div>}
      </div>
    </>
  );
};

export default Promociones;
