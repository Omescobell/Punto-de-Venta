import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css'; // Reusing styles

const Proveedores = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingSupplierId, setEditingSupplierId] = useState(null);

  const initialFormState = {
    contact_person: '',
    name: '',
    phone_number: '',
    rfc: '',
    tax_address: ''
  };

  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('No hay sesión activa');
        setLoading(false);
        return;
      }

      const response = await fetch('/api/suppliers/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        if (response.status === 401) throw new Error('Sesión expirada o no autorizada');
        if (response.status === 403) throw new Error('No tiene permisos para ver proveedores');
        throw new Error('Error al cargar proveedores');
      }

      const data = await response.json();
      setSuppliers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching suppliers:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleEdit = (supplier) => {
    setFormData({
      contact_person: supplier.contact_person,
      name: supplier.name,
      phone_number: supplier.phone_number,
      rfc: supplier.rfc,
      tax_address: supplier.tax_address
    });
    setEditingSupplierId(supplier.id);
    setShowModal(true);
  };

  const openAddModal = () => {
    setFormData(initialFormState);
    setEditingSupplierId(null);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.contact_person) {
      alert('Por favor complete los campos obligatorios (Empresa, Contacto)');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const url = editingSupplierId ? `/api/suppliers/${editingSupplierId}/` : '/api/suppliers/';
      const method = editingSupplierId ? 'PATCH' : 'POST';

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
        setShowModal(false);
        setFormData(initialFormState);
        setEditingSupplierId(null);
        fetchSuppliers();
        alert(editingSupplierId ? 'Proveedor actualizado correctamente' : 'Proveedor creado correctamente');
      } else {
        console.error('Error saving supplier:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al guardar proveedor';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión al guardar proveedor');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este proveedor?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/suppliers/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        fetchSuppliers();
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar proveedor');
      }
    } catch (err) {
      console.error('Error deleting supplier:', err);
      alert('Error de conexión al eliminar proveedor');
    }
  };

  const filteredSuppliers = suppliers.filter(supplier => {
    const search = searchTerm.toLowerCase();
    return (
      (supplier.name || '').toLowerCase().includes(search) ||
      (supplier.contact_person || '').toLowerCase().includes(search) ||
      (supplier.rfc || '').toLowerCase().includes(search)
    );
  });

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
          <button className="button_add" onClick={openAddModal}>
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="Table-Wrapper">
          {error && <div className="alert alert-danger m-3">{error}</div>}
          
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre del contacto</th>
                <th>Empresa</th>
                <th>Telefono</th>
                <th>RFC</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                 <tr><td colSpan="5" className="text-center">Cargando...</td></tr>
              ) : filteredSuppliers.length === 0 ? (
                 <tr><td colSpan="5" className="text-center">No se encontraron proveedores</td></tr>
              ) : (
                filteredSuppliers.map(supplier => (
                  <tr key={supplier.id}>
                    <td>{supplier.contact_person}</td>
                    <td>{supplier.name}</td>
                    <td>{supplier.phone_number}</td>
                    <td>{supplier.rfc}</td>
                    <td>
                      <ActionButtons 
                        onEdit={() => handleEdit(supplier)} 
                        onDelete={() => handleDelete(supplier.id)}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Supplier Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="text-center m-0 w-100">{editingSupplierId ? 'Editar Proveedor' : 'Agregar Proveedor'}</h2>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="contact_person" className="form-label">Nombre del contacto *</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="contact_person" 
                    placeholder="Ej. Juan Pérez"
                    value={formData.contact_person}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div className="row mb-4">
                  <div className="col-8">
                    <label htmlFor="name" className="form-label">Empresa *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="col-4">
                    <label htmlFor="phone_number" className="form-label">Telefono</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="phone_number"
                      value={formData.phone_number}
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
                    <label htmlFor="tax_address" className="form-label">Dirección Fiscal</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="tax_address"
                      value={formData.tax_address}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                
                <div className="row mb-4">
                  <button type="submit" className="btn btn-primary">
                    {editingSupplierId ? 'Guardar Cambios' : 'Guardar Proveedor'}
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

export default Proveedores;
