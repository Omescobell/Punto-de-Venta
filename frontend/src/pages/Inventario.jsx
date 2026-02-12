import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css'; // Reusing styles

const Inventario = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingProductId, setEditingProductId] = useState(null);

  const initialFormState = {
    sku: '',
    name: '',
    supplier: '',
    price: '', // Base price
    tax_rate: '0.16', // Default IVA
    current_stock: '',
    min_stock: ''
  };

  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
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
        
        // Fetch operations in parallel
        const [prodRes, suppRes] = await Promise.all([
          fetch('/api/products/', { headers }),
          fetch('/api/suppliers/', { headers }) // Suppliers needed for dropdown
        ]);

        if (!prodRes.ok) throw new Error('Error al cargar productos');
        // Suppliers fetch might fail if not admin, but we should handle it gracefully or rely on backend permissions
        
        const productsData = await prodRes.json();
        setProducts(Array.isArray(productsData) ? productsData : []);

        if (suppRes.ok) {
          const suppliersData = await suppRes.json();
          setSuppliers(Array.isArray(suppliersData) ? suppliersData : []);
        }

      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const openAddModal = () => {
    setFormData(initialFormState);
    setEditingProductId(null);
    setShowModal(true);
  };

  const handleEdit = (product) => {
    setFormData({
      sku: product.sku,
      name: product.name,
      supplier: product.supplier, // Backend returns ID
      price: product.price,
      tax_rate: product.tax_rate,
      current_stock: product.current_stock,
      min_stock: product.min_stock || ''
    });
    setEditingProductId(product.id);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.sku || !formData.price || !formData.supplier) {
      alert('Por favor complete los campos obligatorios');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const url = editingProductId ? `/api/products/${editingProductId}/` : '/api/products/';
      const method = editingProductId ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        const updatedProduct = data;
        
        // Update local list without full refetch for better UX
        if (editingProductId) {
          setProducts(prev => prev.map(p => p.id === editingProductId ? updatedProduct : p));
        } else {
          setProducts(prev => [updatedProduct, ...prev]);
        }

        setShowModal(false);
        setFormData(initialFormState);
        setEditingProductId(null);
        alert(editingProductId ? 'Producto actualizado correctamente' : 'Producto creado correctamente');
      } else {
        console.error('Error saving product:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al guardar producto';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión al guardar producto');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este producto?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/products/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setProducts(prev => prev.filter(p => p.id !== id));
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar producto');
      }
    } catch (err) {
      console.error('Error deleting product:', err);
      alert('Error de conexión al eliminar producto');
    }
  };

  const filteredProducts = products.filter(product => {
    const search = searchTerm.toLowerCase();
    return (
      (product.name || '').toLowerCase().includes(search) ||
      (product.sku || '').toLowerCase().includes(search)
    );
  });

  // Helper to get supplier name from ID
  const getSupplierName = (id) => {
    const supplier = suppliers.find(s => s.id === id);
    return supplier ? supplier.name : 'Desconocido';
  };

  return (
    <>
      <Navbar activeItem="Inventario" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Producto (Nombre o SKU)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button className="button_add" onClick={openAddModal}>
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="Table-Wrapper">
          {error && <div className="alert alert-danger m-3">{error}</div>}

          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Producto</th>
                <th>Precio Final</th>
                <th>Stock</th>
                <th>Proveedor</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="text-center">Cargando...</td></tr>
              ) : filteredProducts.length === 0 ? (
                <tr><td colSpan="6" className="text-center">No se encontraron productos</td></tr>
              ) : (
                filteredProducts.map(product => (
                  <tr key={product.id}>
                    <td>{product.sku}</td>
                    <td>{product.name}</td>
                    <td>${Number(product.final_price).toFixed(2)}</td>
                    <td>{product.current_stock}</td>
                    <td>{getSupplierName(product.supplier)}</td>
                    <td>
                      <ActionButtons 
                        onEdit={() => handleEdit(product)} 
                        onDelete={() => handleDelete(product.id)}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Product Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="text-center m-0 w-100">{editingProductId ? 'Editar Producto' : 'Agregar Producto'}</h2>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              
              <form onSubmit={handleSubmit}>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="sku" className="form-label">SKU *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="sku" 
                      value={formData.sku}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="name" className="form-label">Nombre *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="name" 
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>
                
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="supplier" className="form-label">Proveedor *</label>
                    <select 
                      className="form-select"
                      id="supplier"
                      value={formData.supplier}
                      onChange={handleInputChange}
                      required
                    >
                      <option value="">Seleccionar...</option>
                      {suppliers.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="tax_rate" className="form-label">Impuesto *</label>
                    <select 
                      className="form-select"
                      id="tax_rate"
                      value={formData.tax_rate}
                      onChange={handleInputChange}
                    >
                      <option value="0.16">IVA General (16%)</option>
                      <option value="0.08">IVA Fronterizo (8%)</option>
                      <option value="0.00">Tasa Cero (0%)</option>
                      <option value="EXENT">Exento</option>
                    </select>
                  </div>
                </div>
                
                <div className="row mb-3">
                  <div className="col-md-4">
                    <label htmlFor="price" className="form-label">Precio Base *</label>
                    <div className="input-group">
                      <span className="input-group-text">$</span>
                      <input 
                        type="number" 
                        step="0.01"
                        className="form-control" 
                        id="price" 
                        value={formData.price}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <label htmlFor="current_stock" className="form-label">Stock Actual *</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="current_stock" 
                      value={formData.current_stock}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label htmlFor="min_stock" className="form-label">Stock Mínimo</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="min_stock" 
                      value={formData.min_stock}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="d-grid gap-2 mt-4">
                  <button type="submit" className="button_Modal">
                    {editingProductId ? 'Guardar Cambios' : 'Agregar Producto'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Inventario;
