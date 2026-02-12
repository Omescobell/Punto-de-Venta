import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css';

const Usuarios = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingUserId, setEditingUserId] = useState(null);
  
  // Initial form state
  const initialFormState = {
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    address: '',
    role: 'EMPLOYEE',
    phone_number: ''
  };

  const [formData, setFormData] = useState(initialFormState);

  const subHeaderItems = [
    { name: 'Usuarios', path: '/usuarios' },
    { name: 'ChatBot', path: '/chatbot' }
  ];

  // Fetch users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('No hay sesión activa');
        setLoading(false);
        return;
      }

      // Check if we are using the /auth or /api proxy. 
      // Based on previous login debugging, endpoints are at /api/users/ or similar?
      // Re-reading: Login was at /auth/login. Users are at /users/. 
      // The proxy /api -> target/api handles /api/users/ which maps to target/api/users/.
      // But wait, the backend README said:
      // Endpoint: /users/
      // Base URL: /api/
      // So valid URL is /api/users/
      
      const response = await fetch('/api/users/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        if (response.status === 401) throw new Error('Sesión expirada o no autorizada');
        if (response.status === 403) throw new Error('No tiene permisos para ver usuarios');
        throw new Error('Error al cargar usuarios');
      }

      const data = await response.json();
      setUsers(Array.isArray(data) ? data : []); // Ensure it's an array
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user) => {
    setFormData({
      username: user.username,
      email: user.email,
      password: '', // Do not populate password
      first_name: user.first_name,
      last_name: user.last_name,
      address: user.address || '',
      role: user.role,
      phone_number: user.phone_number || ''
    });
    setEditingUserId(user.id);
    setShowModal(true);
  };

  const openAddModal = () => {
    setFormData(initialFormState);
    setEditingUserId(null);
    setShowModal(true);
  };

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Validation
    const requiredFields = ['username', 'email', 'first_name', 'last_name', 'role'];
    if (!editingUserId) requiredFields.push('password'); // Password required only for new users

    const missing = requiredFields.filter(field => !formData[field]);
    if (missing.length > 0) {
      alert(`Por favor complete los campos obligatorios: ${missing.join(', ')}`);
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const url = editingUserId ? `/api/users/${editingUserId}/` : '/api/users/';
      const method = editingUserId ? 'PATCH' : 'POST';
      
      // Prepare payload
      const payload = { ...formData };
      if (editingUserId && !payload.password) {
        delete payload.password; // Don't send empty password on update
      }

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        // Success
        setShowModal(false);
        setFormData(initialFormState);
        setEditingUserId(null);
        fetchUsers(); // Refresh list
        alert(editingUserId ? 'Usuario actualizado correctamente' : 'Usuario creado correctamente');
      } else {
        // Error handling
        console.error('Error saving user:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al guardar usuario';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión al guardar usuario');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este usuario?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/users/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        fetchUsers(); // Refresh list
      } else {
        const data = await response.json();
        alert(data.detail || 'Error al eliminar usuario');
      }
    } catch (err) {
      console.error('Error deleting user:', err);
      alert('Error de conexión al eliminar usuario');
    }
  };

  // Filter users based on search term
  const filteredUsers = users.filter(user => {
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.toLowerCase();
    const search = searchTerm.toLowerCase();
    return fullName.includes(search) || user.email?.toLowerCase().includes(search) || user.username?.toLowerCase().includes(search);
  });

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
            onClick={openAddModal}
          >
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="Table-Wrapper">
          {error && <div className="alert alert-danger m-3">{error}</div>}
          
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre Completo</th>
                <th>Usuario</th>
                <th>Correo</th>
                <th>Rol</th>
                <th style={{ width: '200px' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="5" className="text-center">Cargando...</td></tr>
              ) : filteredUsers.length === 0 ? (
                <tr><td colSpan="5" className="text-center">No se encontraron usuarios</td></tr>
              ) : (
                filteredUsers.map(user => (
                  <tr key={user.id}>
                    <td>{user.first_name} {user.last_name}</td>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>{user.role}</td>
                    <td>
                      <ActionButtons 
                        onEdit={() => handleEdit(user)} 
                        onDelete={() => handleDelete(user.id)} 
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered modal-lg"> {/* Increased size for more fields */}
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="text-center m-0 w-100">{editingUserId ? 'Editar Usuario' : 'Agregar Usuario'}</h2>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              
              <form onSubmit={handleSubmit}>
                {/* Row 1: Names */}
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

                {/* Row 2: Account Info */}
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="username" className="form-label">Nombre de Usuario *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="username" 
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="email" className="form-label">Correo Electrónico *</label>
                    <input 
                      type="email" 
                      className="form-control" 
                      id="email" 
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                {/* Row 3: Security & Role */}
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="password" className="form-label">
                      Contraseña {editingUserId ? '(Opcional)' : '*'}
                    </label>
                    <input 
                      type="password" 
                      className="form-control" 
                      id="password" 
                      value={formData.password}
                      onChange={handleInputChange}
                      required={!editingUserId}
                      placeholder={editingUserId ? 'Dejar en blanco para mantener actual' : ''}
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="role" className="form-label">Rol *</label>
                    <select 
                      className="form-select"
                      id="role"
                      value={formData.role}
                      onChange={handleInputChange}
                    >
                      <option value="EMPLOYEE">Empleado</option>
                      <option value="ADMIN">Administrador</option>
                      <option value="OWNER">Dueño</option>
                    </select>
                  </div>
                </div>

                {/* Row 4: Contact Info (Optional) */}
                <div className="row mb-4">
                  <div className="col-md-6">
                    <label htmlFor="phone_number" className="form-label">Teléfono</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="phone_number"
                      value={formData.phone_number}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="address" className="form-label">Dirección</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      id="address"
                      value={formData.address}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="d-grid gap-2">
                  <button type="submit" className="btn btn-primary">
                    {editingUserId ? 'Guardar Cambios' : 'Guardar Usuario'}
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

export default Usuarios;
