import { useEffect, useRef } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import { Chart } from 'chart.js/auto'; // Import Chart.js
import '../styles/Metricas-Productos.css';

const MetricasProductos = () => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  // Subheader configuration
  const subHeaderItems = [
    { name: 'Ventas', path: '/metricas' },
    { name: 'Productos', path: '/metricas-productos' }
  ];

  useEffect(() => {
    if (chartRef.current) {
      // Destroy previous instance if exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Producto 1', 'Producto 2', 'Producto 3', 'Producto 4', 'Producto 5'],
            datasets: [{
                data: [300, 150, 100, 80, 50],
                backgroundColor: [
                    '#E74C3C', // Rojo
                    '#F39C12', // Naranja
                    '#3498DB', // Azul
                    '#BDF589', // Verde claro
                    '#9B59B6'  // Morado
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom', // Adjusted to visible
                }
            }
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  return (
    <>
      <Navbar activeItem="Metricas" />
      {/* Use standard SubHeader component for consistency, overriding active item */}
      {/* Actually, custom HTML had specific structure. Let's try to use the reusable SubHeader if possible, 
          but the HTML has "Ventas" and "Productos" as sub-items. 
          Our SubHeader component supports items prop. */}
      <SubHeader items={subHeaderItems} activeItem="Productos" />

      <div className="Main-Container">
        {/* Título Periodo */}
        <div className="row">
            <div className="col-12">
                <h1 className="periodo-title">Periodo</h1>
            </div>
        </div>

        <div className="row">
            {/* Columna Izquierda: Inputs y Tabla */}
            <div className="col-md-5 col-lg-4">
                
                {/* Inputs de Fecha */}
                <div className="row mb-5">
                    <div className="col-6">
                        <label className="date-label">Fecha de inicio</label>
                        <div className="date-group">
                            <input type="date" className="date-input-box" placeholder="DD" />
                        </div>
                    </div>
                    <div className="col-6">
                        <label className="date-label">Fecha de Fin</label>
                        <div className="date-group">
                            <input type="date" className="date-input-box" placeholder="DD" />
                        </div>
                    </div>
                </div>

                <select className="selecter mb-4">
                    <option value="">Todos</option>
                    <option value="">Mas Vendidos</option>
                    <option value="">Menos Vendidos</option>
                </select>
                
                {/* Tabla */}
                <div className="tabla-container">
                    {/* Using Custom-Table from General.css for consistency */}
                    <table className="table table-bordered Custom-Table">
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Promedio de Ventas</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>Producto 1</td><td>$300</td></tr>
                            <tr><td>Producto 2</td><td>$150</td></tr>
                            <tr><td>Producto 3</td><td>$100</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Columna Derecha: Gráfica */}
            <div className="col-md-7 col-lg-8">
                <div className="chart-container">
                    <canvas ref={chartRef}></canvas>
                </div>
            </div>
        </div>
    </div>
    </>
  );
};

export default MetricasProductos;
