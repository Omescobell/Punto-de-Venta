import React from 'react';
// Asegúrate de importar el CSS si estás en un entorno modular,
// o que el CSS global (arriba) esté cargado en el index.html.

function Toolbar() {
    return (
        <nav className="custom-navbar">
            <ul className="nav-list">
                {/* Agregamos la clase 'active' condicionalmente según la ruta si fuera necesario */}
                <li className="nav-item active">
                    <a href="/View/Usuarios">Usuarios</a>
                </li>
                <li className="nav-item">
                    <a href="#">Proveedores</a>
                </li>
                <li className="nav-item">
                    <a href="#">Ventas</a>
                </li>
                <li className="nav-item">
                    <a href="#">Inventario</a>
                </li>
                <li className="nav-item">
                    <a href="#">Promociones</a>
                </li>  
                <li className="nav-item">
                    <a href="#">Clientes</a>
                </li>  
                <li className="nav-item">
                    <a href="#">Métricas</a>
                </li>  
            </ul>
        </nav>
    );
}

export default Toolbar;