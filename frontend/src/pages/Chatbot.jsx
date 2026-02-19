import { useState, useEffect } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import '../styles/Usuarios.css';
import '../styles/General.css';

const Chatbot = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  
  // Data State
  const [chatbotUsers, setChatbotUsers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form State
  const initialFormState = {
    employee_name: '', // We store the name string as confirmed by plan
    phone: '' // Maps to mobile_number
  };
  const [formData, setFormData] = useState(initialFormState);

  const subHeaderItems = [
    { name: 'Usuarios', path: '/usuarios' },
    { name: 'ChatBot', path: '/chatbot' }
  ];

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
      
      const [chatUsersRes, employeesRes] = await Promise.all([
        fetch('/api/chatbotusers/', { headers }),
        fetch('/api/users/', { headers })
      ]);

      if (chatUsersRes.ok) {
        const data = await chatUsersRes.json();
        setChatbotUsers(Array.isArray(data) ? data : []);
      } else {
        if (chatUsersRes.status === 403) setError('No tiene permisos para ver usuarios de chatbot');
      }

      if (employeesRes.ok) {
        const data = await employeesRes.json();
        setEmployees(Array.isArray(data) ? data : []);
      }

    } catch (err) {
      console.error('Error fetching data:', err);
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

  // When selecting an employee from dropdown, we set the name
  const handleEmployeeSelect = (e) => {
    const selectedId = e.target.value;
    const employee = employees.find(emp => emp.id === parseInt(selectedId));
    if (employee) {
      setFormData(prev => ({
        ...prev,
        employee_name: `${employee.first_name} ${employee.last_name}`
      }));
    } else {
      setFormData(prev => ({ ...prev, employee_name: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.employee_name || !formData.phone) {
      alert('Por favor seleccione un empleado e ingrese el teléfono');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = {
        name: formData.employee_name,
        mobile_number: formData.phone
      };

      const response = await fetch('/api/chatbotusers/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        setChatbotUsers(prev => [...prev, data]);
        setShowModal(false);
        setFormData(initialFormState);
        alert('Usuario agregado a ChatBot correctamente');
      } else {
        console.error('Error creating chatbot user:', data);
        const errorMessage = Object.values(data).flat().join('\n') || 'Error al agregar usuario';
        alert(errorMessage);
      }
    } catch (err) {
      console.error('Error submitting form:', err);
      alert('Error de conexión');
    }
  };

  const handleDelete = async (mobile_number) => {
    if (!window.confirm(`¿Está seguro de eliminar el número ${mobile_number} del chatbot?`)) return;

    try {
      const token = localStorage.getItem('access_token');
      // The endpoint uses mobile_number as ID
      const response = await fetch(`/api/chatbotusers/${mobile_number}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setChatbotUsers(prev => prev.filter(u => u.mobile_number !== mobile_number));
      } else {
        alert('Error al eliminar usuario');
      }
    } catch (err) {
      console.error('Error deleting chatbot user:', err);
      alert('Error de conexión');
    }
  };

  const filteredUsers = chatbotUsers.filter(user => {
    const search = searchTerm.toLowerCase();
    return (
      (user.name || '').toLowerCase().includes(search) ||
      (user.mobile_number || '').includes(search)
    );
  });

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
          {error && <div className="alert alert-danger m-3">{error}</div>}
          
          <table className="table table-bordered Custom-Table">
            <thead>
              <tr>
                <th>Nombre Completo</th>
                <th>Telefono</th>
                <th style={{ width: '200px' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="3" className="text-center">Cargando...</td></tr>
              ) : filteredUsers.length === 0 ? (
                <tr><td colSpan="3" className="text-center">No se encontraron usuarios de chatbot</td></tr>
              ) : (
                filteredUsers.map(user => (
                  <tr key={user.mobile_number}>
                    <td>{user.name}</td>
                    <td>{user.mobile_number}</td>
                    <ActionButtons 
                       onDelete={() => handleDelete(user.mobile_number)}
                    />
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add ChatBot User Modal */}
      <div className={`modal fade ${showModal ? 'show' : ''}`} 
           style={{ display: showModal ? 'block' : 'none', backgroundColor: 'rgba(0,0,0,0.5)' }}
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
                      onChange={handleEmployeeSelect}
                      defaultValue=""
                    >
                      <option value="">Seleccionar...</option>
                      {employees.map(emp => (
                        <option key={emp.id} value={emp.id}>
                          {emp.first_name} {emp.last_name} ({emp.email})
                        </option>
                      ))}
                    </select>
                    {formData.employee_name && <small className="text-success">Seleccionado: {formData.employee_name}</small>}
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
                    placeholder="Ej: 5215512345678"
                  />
                  <small className="text-muted">Incluya código de país si es necesario</small>
                </div>
                
                <div className="row mb-3">
                  <button type="submit" className="button_Modal">Agregar a ChatBot</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Chatbot;
