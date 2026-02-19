import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Promociones.css';

const Promociones = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBirthdayModal, setShowBirthdayModal] = useState(false);

  // Data State
  const [promotions, setPromotions] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form State
  const initialPromoState = {
    name: '',
    description: '',
    target_audience: 'ALL', // Maps to 'accessLevel'
    discount_percent: '',
    start_date: '',
    end_date: '',
    product: ''
  };

  const [promoData, setPromoData] = useState(initialPromoState);

  // Birthday Config (UI Only for now)
  const [birthdayData, setBirthdayData] = useState({
    type: '',
    minSpend: '',
    discount: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      setError('No hay sesión activa');
      setLoading(false);
      return;
    }

    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [promosRes, prodsRes] = await Promise.all([
        fetch('/api/promotions/', { headers }),
        fetch('/api/products/', { headers })
      ]);

      if (promosRes.ok) {
        const data = await promosRes.json();
        setPromotions(Array.isArray(data) ? data : []);
      } else {
        // If 403, maybe not admin?
        if (promosRes.status === 403) throw new Error('No tiene permisos para ver promociones');
      }

      if (prodsRes.ok) {
        const data = await prodsRes.json();
        setProducts(Array.isArray(data) ? data : []);
      }

    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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

  const handlePromoSubmit = async (e) => {
    e.preventDefault();
    if (!promoData.name || !promoData.product || !promoData.discount_percent || !promoData.start_date || !promoData.end_date) {
      alert('Por favor complete los campos obligatorios');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/promotions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(promoData)
      });

      const data = await response.json();

      if (response.ok) {
        setPromotions(prev => [...prev, data]);
        setShowAddModal(false);
        setPromoData(initialPromoState);
        alert('Promoción creada correctamente');
      } else {
        console.error('Error creating promotion:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al crear promoción';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar esta promoción?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/promotions/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setPromotions(prev => prev.filter(p => p.id !== id));
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar promoción');
      }
    } catch (err) {
      console.error('Error deleting promotion:', err);
      alert('Error de conexión');
    }
  };

  const handleBirthdaySubmit = (e) => {
    e.preventDefault();
    // Placeholder: No backend endpoint yet
    console.log('Birthday Config:', birthdayData);
    setShowBirthdayModal(false);
    alert('Configuración guardada (Localmente)');
  };

  const getProductName = (id) => {
    const product = products.find(p => p.id === id);
    return product ? product.name : 'Desconocido';
  };

  const filteredPromotions = promotions.filter(promo => {
    const search = searchTerm.toLowerCase();
    return (
      (promo.name || '').toLowerCase().includes(search) ||
      (promo.description || '').toLowerCase().includes(search)
    );
  });

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
              Promoción
              <i className="bi bi-plus-lg"></i>
            </button>
            <button className="button_add wide" style={{ backgroundColor: '#6c757d' }} onClick={() => setShowBirthdayModal(true)}>
              <i className="bi bi-gift"></i>
            </button>
          </div>
        </div>

        <div className="Table-Wrapper">
          {error && <div className="alert alert-danger m-3">{error}</div>}
          
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Periodo</th>
                <th>Descuento</th>
                <th>Producto</th>
                <th>Clientes</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="text-center">Cargando...</td></tr>
              ) : filteredPromotions.length === 0 ? (
                <tr><td colSpan="6" className="text-center">No se encontraron promociones activas</td></tr>
              ) : (
                filteredPromotions.map(promo => (
                  <tr key={promo.id}>
                    <td>{promo.name}</td>
                    <td>{promo.start_date} - {promo.end_date}</td>
                    <td>{Number(promo.discount_percent).toFixed(0)}%</td>
                    <td>{getProductName(promo.product)}</td>
                    <td>{promo.target_audience === 'ALL' ? 'Todos' : 'Frecuentes'}</td>
                    <ActionButtons>
                      <button className="button_delete" onClick={() => handleDelete(promo.id)} title="Eliminar">
                        <i className="bi bi-trash"></i>
                      </button>
                    </ActionButtons>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Promotion Modal */}
      <div className={`modal fade ${showAddModal ? 'show' : ''}`} 
           style={{ display: showAddModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Agregar Promoción</h2>
              
              <form onSubmit={handlePromoSubmit}>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="name" className="form-label">Nombre *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="name"
                      value={promoData.name}
                      onChange={handlePromoChange}
                      required
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
                    <label htmlFor="target_audience" className="form-label">Clientes</label>
                    <select 
                      className="form-select" 
                      id="target_audience"
                      value={promoData.target_audience}
                      onChange={handlePromoChange}
                    >
                      <option value="ALL">Todos</option>
                      <option value="FREQUENT_ONLY">Solo Frecuentes</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="discount_percent" className="form-label">Descuento (%) *</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="discount_percent"
                      value={promoData.discount_percent}
                      onChange={handlePromoChange}
                      required
                    />
                  </div>
                </div>

                <div className="row mb-4">
                  <div className="col-md-6">
                    <label className="form-label">Vigencia (Inicio - Fin) *</label>
                    <div className="d-flex gap-2">
                       <input 
                        type="date" 
                        className="form-control" 
                        id="start_date"
                        value={promoData.start_date}
                        onChange={handlePromoChange}
                        required
                      />
                      <input 
                        type="date" 
                        className="form-control" 
                        id="end_date"
                        value={promoData.end_date}
                        onChange={handlePromoChange}
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="product" className="form-label">Producto *</label>
                    <select 
                      className="form-select" 
                      id="product"
                      value={promoData.product}
                      onChange={handlePromoChange}
                      required
                    >
                      <option value="">Seleccionar...</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</option>
                      ))}
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
      </div>

      {/* Birthday Config Modal */}
      <div className={`modal fade ${showBirthdayModal ? 'show' : ''}`} 
           style={{ display: showBirthdayModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">Configurar Cumpleaños</h2>
              
              <form onSubmit={handleBirthdaySubmit}>
                <div className="row mb-4">
                  <div className="alert alert-info">
                    Nota: La configuración de cumpleaños se aplica automáticamente por el sistema. 
                    <br/>
                    (Esta funcionalidad está en desarrollo en el backend)
                  </div>
                </div>

                <div className="row mb-3">
                  <button type="button" className="button_Modal" onClick={() => setShowBirthdayModal(false)}>Cerrar</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Promociones;
