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
          <button className="button_add" onClick={openAddModal}>
            <i className="bi bi-plus-lg"></i>
          </button>
        </div>

        <div className="w-full sm:w-[90%] sm:max-w-[1200px] mx-auto overflow-x-auto pb-4 px-2 sm:px-0">
          {error && <div className="bg-[#f8d7da] border border-[#f5c6cb] text-[#721c24] px-4 py-3 rounded mb-3">{error}</div>}
          
          <table className="w-full bg-white border border-[#dee2e6] text-left border-collapse min-w-[700px]">
            <thead>
              <tr>
                <th className="bg-[#f2f2f2] text-[#333] font-bold text-[14px] md:text-[18px] align-middle border-b-2 border-[#ddd] h-[50px] px-2 md:pl-[15px] whitespace-nowrap">Nombre Completo</th>
                <th className="bg-[#f2f2f2] text-[#333] font-bold text-[14px] md:text-[18px] align-middle border-b-2 border-[#ddd] h-[50px] px-2 md:pl-[15px] whitespace-nowrap">Usuario</th>
                <th className="bg-[#f2f2f2] text-[#333] font-bold text-[14px] md:text-[18px] align-middle border-b-2 border-[#ddd] h-[50px] px-2 md:pl-[15px] whitespace-nowrap">Correo</th>
                <th className="bg-[#f2f2f2] text-[#333] font-bold text-[14px] md:text-[18px] align-middle border-b-2 border-[#ddd] h-[50px] px-2 md:pl-[15px] whitespace-nowrap">Rol</th>
                <th className="bg-[#f2f2f2] text-[#333] font-bold text-[14px] md:text-[18px] align-middle border-b-2 border-[#ddd] h-[50px] px-2 md:pl-[15px] whitespace-nowrap" style={{ width: '200px' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="5" className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-center text-[#212529]">Cargando...</td></tr>
              ) : filteredUsers.length === 0 ? (
                <tr><td colSpan="5" className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-center text-[#212529]">No se encontraron usuarios</td></tr>
              ) : (
                filteredUsers.map(user => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-[14px] md:text-base text-[#212529] whitespace-nowrap">{user.first_name} {user.last_name}</td>
                    <td className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-[14px] md:text-base text-[#212529] whitespace-nowrap">{user.username}</td>
                    <td className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-[14px] md:text-base text-[#212529] whitespace-nowrap">{user.email}</td>
                    <td className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-[14px] md:text-base text-[#212529] whitespace-nowrap">{user.role}</td>
                    <td className="bg-white h-[60px] align-middle px-2 py-2 md:pl-[15px] border-b border-[#eee] text-[14px] md:text-base text-[#212529] whitespace-nowrap">
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

      {/* Add/Edit User Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 transition-opacity p-4 sm:p-0" tabIndex="-1">
          <div className="w-full max-w-4xl sm:mx-4 relative bg-[#b2b2b2] rounded-[10px] sm:rounded-[20px] p-4 sm:p-[30px] my-auto max-h-[95vh] overflow-y-auto shadow-2xl">
            <div className="bg-white rounded-[10px] sm:rounded-[20px] p-4 sm:p-[30px] w-full">
              <div className="flex justify-between flex-row items-center mb-6 sm:mb-[30px]">
                <h2 className="text-center font-bold text-[#1e1e1e] text-xl sm:text-3xl w-full m-0">
                  {editingUserId ? 'Editar Usuario' : 'Agregar Usuario'}
                </h2>
                <button type="button" className="text-2xl sm:text-3xl font-bold bg-transparent border-none cursor-pointer absolute right-4 sm:right-[45px]" onClick={() => setShowModal(false)}>&times;</button>
              </div>
              
              <form onSubmit={handleSubmit}>
                {/* Row 1: Names */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="first_name" className="block font-medium text-[#333] mb-1">Nombre(s) *</label>
                    <input 
                      type="text" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="first_name" 
                      value={formData.first_name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block font-medium text-[#333] mb-1">Apellidos *</label>
                    <input 
                      type="text" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="last_name" 
                      value={formData.last_name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                {/* Row 2: Account Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="username" className="block font-medium text-[#333] mb-1">Nombre de Usuario *</label>
                    <input 
                      type="text" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="username" 
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block font-medium text-[#333] mb-1">Correo Electrónico *</label>
                    <input 
                      type="email" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="email" 
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                {/* Row 3: Security & Role */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="password" className="block font-medium text-[#333] mb-1">
                      Contraseña {editingUserId ? '(Opcional)' : '*'}
                    </label>
                    <input 
                      type="password" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="password" 
                      value={formData.password}
                      onChange={handleInputChange}
                      required={!editingUserId}
                      placeholder={editingUserId ? 'Dejar en blanco para mantener actual' : ''}
                    />
                  </div>
                  <div>
                    <label htmlFor="role" className="block font-medium text-[#333] mb-1">Rol *</label>
                    <select 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]"
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="phone_number" className="block font-medium text-[#333] mb-1">Teléfono</label>
                    <div className="flex flex-row gap-2.5 w-full">
                      <select className="w-[35%] md:w-[30%] text-sm md:text-base text-black rounded-lg border border-white bg-[#ddd] p-1.5 md:p-2.5 outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff] truncate">
                        <option value="">Sel...</option>
                        <option value="1">+1 (US)</option>
                        <option value="1">+1 (CA)</option>
                        <option value="34">+34 (ES)</option>
                        <option value="51">+51 (PE)</option>
                        <option value="52">+52 (MX)</option>
                        <option value="53">+53 (CU)</option>
                        <option value="54">+54 (AR)</option>
                        <option value="55">+55 (BR)</option>
                        <option value="57">+57 (CO)</option>
                        <option value="58">+58 (VE)</option>
                        <option value="503">+503 (SV)</option>
                        <option value="504">+504 (HN)</option>
                        <option value="505">+505 (NI)</option>
                        <option value="506">+506 (CR)</option>
                        <option value="507">+507 (PA)</option>
                        <option value="508">+508 (DO)</option>
                        <option value="509">+509 (HT)</option>
                        <option value="591">+591 (BO)</option>
                        <option value="593">+593 (EC)</option>
                        <option value="595">+595 (PY)</option>
                        <option value="598">+598 (UY)</option>
                        <option value="599">+599 (CW)</option>
                      </select>
                      <input 
                        type="number" 
                        className="w-[65%] md:w-[70%] rounded-lg border border-white bg-[#ddd] p-1.5 md:p-2.5 text-sm md:text-base outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        id="phone_number"
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        placeholder="15512345678"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="address" className="block font-medium text-[#333] mb-1">Dirección</label>
                    <input 
                      type="text" 
                      className="w-full rounded-lg border border-white bg-[#ddd] p-1.5 md:p-2.5 text-sm md:text-base outline-none focus:outline-none focus:ring-[1px] focus:ring-[#007bff] focus:border-[#007bff]" 
                      id="address"
                      value={formData.address}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="w-full mt-2 sm:mt-5">
                  <button type="submit" className="w-full bg-[#2c2c2c] text-white font-bold py-3 rounded-lg flex justify-center items-center hover:opacity-90 transition-opacity">
                    {editingUserId ? 'Guardar Cambios' : 'Guardar Usuario'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Usuarios;
