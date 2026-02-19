import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Clientes.css';

const Clientes = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  
  // Data State
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);

  // Form State
  const initialFormState = {
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    birth_date: ''
  };
  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) {
      setError('No hay sesión activa');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/customers/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setCustomers(Array.isArray(data) ? data : []);
      } else {
        if (response.status === 403) setError('No tiene permisos para ver clientes');
        else setError('Error al cargar clientes');
      }
    } catch (err) {
      console.error('Error fetching customers:', err);
      setError('Error de conexión');
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

  const openAddModal = () => {
    setFormData(initialFormState);
    setEditingId(null);
    setShowModal(true);
  };

  const openEditModal = (customer) => {
    setFormData({
      first_name: customer.first_name || '',
      last_name: customer.last_name || '',
      email: customer.email || '',
      phone_number: customer.phone_number || '',
      birth_date: customer.birth_date || ''
    });
    setEditingId(customer.id);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.first_name || !formData.last_name) {
      alert('Nombre y Apellidos son obligatorios');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const url = editingId ? `/api/customers/${editingId}/` : '/api/customers/';
      const method = editingId ? 'PATCH' : 'POST';

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
        if (editingId) {
          setCustomers(prev => prev.map(c => c.id === editingId ? data : c));
          alert('Cliente actualizado correctamente');
        } else {
          setCustomers(prev => [...prev, data]);
          alert('Cliente agregado correctamente');
        }
        setShowModal(false);
      } else {
        console.error('Error saving customer:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al guardar cliente';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este cliente?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/customers/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok || response.status === 204) {
        setCustomers(prev => prev.filter(c => c.id !== id));
      } else {
        alert('Error al eliminar cliente');
      }
    } catch (err) {
      console.error('Error deleting customer:', err);
      alert('Error de conexión');
    }
  };

  const filteredCustomers = customers.filter(customer => {
    const search = searchTerm.toLowerCase();
    const fullName = `${customer.first_name} ${customer.last_name}`.toLowerCase();
    return (
      fullName.includes(search) ||
      (customer.email || '').toLowerCase().includes(search) ||
      (customer.phone_number || '').includes(search)
    );
  });

  return (
    <>
      <Navbar activeItem="Clientes" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Cliente"
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
                <th>Nombre</th>
                <th>Telefono</th>
                <th>Cumpleaños</th>
                <th>Correo</th>
                <th style={{ width: '200px' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="5" className="text-center">Cargando...</td></tr>
              ) : filteredCustomers.length === 0 ? (
                <tr><td colSpan="5" className="text-center">No se encontraron clientes</td></tr>
              ) : (
                filteredCustomers.map(customer => (
                  <tr key={customer.id}>
                    <td>{customer.first_name} {customer.last_name}</td>
                    <td>{customer.phone_number}</td>
                    <td>{customer.birth_date}</td>
                    <td>{customer.email}</td>
                    <ActionButtons 
                      onEdit={() => openEditModal(customer)}
                      onDelete={() => handleDelete(customer.id)}
                    />
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Client Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body p-4">
              <h2 className="text-center mb-4">{editingId ? 'Editar Cliente' : 'Agregar Cliente'}</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="first_name" className="form-label">Nombre(s) *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="last_name" className="form-label">Apellidos *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="birth_date" className="form-label">Fecha de cumpleaños</label>
                    <input 
                      type="date" 
                      className="form-control" 
                      id="birth_date"
                      value={formData.birth_date}
                      onChange={handleInputChange}
                    />
                  </div>
                  
                  <div className="col-md-6">
                    <label htmlFor="phone_number" className="form-label">Teléfono</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      id="phone_number"
                      value={formData.phone_number}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="row mb-4">
                  <label htmlFor="email" className="form-label">Correo electrónico</label>
                  <input 
                    type="email" 
                    className="form-control" 
                    id="email"
                    value={formData.email}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="d-grid mt-4">
                  <button type="submit" className="button_Modal">
                    {editingId ? 'Guardar Cambios' : 'Agregar Cliente'}
                  </button>
                  <button type="button" className="btn btn-secondary mt-2" onClick={() => setShowModal(false)}>
                    Cancelar
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

export default Clientes;
