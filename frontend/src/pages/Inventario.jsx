import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Clientes.css';

const Inventario = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    supplier: '',
    quantity: '',
    price: '',
    brand: '',
    sku: ''
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
    console.log('Product added:', formData);
    setShowModal(false);
  };

  return (
    <>
      <Navbar activeItem="Inventario" />
      
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
                <th>Producto</th>
                <th>SKU</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Proveedor</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Manzana</td>
                <td>SKU123</td>
                <td>10</td>
                <td>15</td>
                <td>Proveedor 1</td>
                <ActionButtons />
              </tr>
              <tr>
                <td>Manzana</td>
                <td>SKU123</td>
                <td>10</td>
                <td>15</td>
                <td>Proveedor 1</td>
                <ActionButtons />
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Product Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Producto</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="row mb-3">
                  <label htmlFor="name" className="form-label">Nombre</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="name" 
                    placeholder="Ej. Manzana"
                    value={formData.name}
                    onChange={handleInputChange}
                  />
                </div>
                
                <div className="row mb-4 g-3">
                  <div className="col-8">
                    <label htmlFor="supplier" className="form-label">Proveedor</label>
                    <select 
                      className="form-select"
                      id="supplier"
                      value={formData.supplier}
                      onChange={handleInputChange}
                    >
                      <option value="">Seleccionar...</option>
                      <option value="1">Proveedor 1</option>
                      <option value="2">Proveedor 2</option>
                      <option value="3">Proveedor 3</option>
                    </select>
                  </div>
                  <div className="col-4">
                    <label htmlFor="quantity" className="form-label">Cantidad</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="quantity" 
                      placeholder="Ej. 10"
                      value={formData.quantity}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="row mb-4 g-3">
                  <div className="col-6">
                    <label htmlFor="price" className="form-label">Precio</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="price" 
                      placeholder="Ej. 15"
                      value={formData.price}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="col-6">
                    <label htmlFor="brand" className="form-label">Marca</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="brand" 
                      placeholder="Ej. ECOR"
                      value={formData.brand}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="col-12 mb-3">
                  <label htmlFor="sku" className="form-label">SKU</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="sku" 
                    placeholder="Ej. SKU123"
                    value={formData.sku}
                    onChange={handleInputChange}
                  />
                </div>
                
                <div className="mb-3">
                  <button type="submit" className="button_Modal">Agregar Producto</button>
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

export default Inventario;
