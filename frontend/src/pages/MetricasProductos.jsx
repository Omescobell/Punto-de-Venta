import { useEffect, useRef, useState } from 'react';
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

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [criterion, setCriterion] = useState('most'); // 'most', 'least', 'both' etc. Custom select has 'Mas Vendidos' or 'Menos Vendidos'
  const [productData, setProductData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchProductRanking = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      let url = '/api/analytics/product-ranking/';
      const params = new URLSearchParams();
      params.append('limit', '5'); // Fetch top 5
      if (criterion) params.append('criterion', criterion);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const queryString = params.toString();
      if (queryString) {
        url += `?${queryString}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        let errorMsg = 'Error al cargar métricas de productos';
        try {
          const errData = await response.json();
          if (errData.error) errorMsg = errData.error;
          else if (typeof errData === 'string') errorMsg = errData;
        } catch (e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      // The API returns most_sold or least_sold array based on criterion, or if no items: simple detail object.
      let items = [];
      if (data.results) {
         if (criterion === 'most') {
             items = data.results.most_sold || [];
         } else if (criterion === 'least') {
             items = data.results.least_sold || [];
         }
      }
      setProductData(items);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductRanking();
  }, [startDate, endDate, criterion]);

  useEffect(() => {
    if (chartRef.current && productData?.length > 0) {
      // Destroy previous instance if exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      const labels = productData.map(p => p.product_name);
      // We can use units_sold or revenue. Let's use revenue for consistency with sales.
      const dataValues = productData.map(p => parseFloat(p.revenue));

      chartInstance.current = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: dataValues,
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
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      let label = context.label || '';
                      if (label) {
                        label += ': ';
                      }
                      if (context.parsed !== null) {
                        label += new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(context.parsed);
                      }
                      return label;
                    }
                  }
                }
            }
        }
      });
    } else if (chartRef.current && productData?.length === 0) {
      // Clear chart if no data
      if (chartInstance.current) {
        chartInstance.current.destroy();
        chartInstance.current = null;
      }
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [productData]);

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
                            <input 
                              type="date" 
                              className="date-input-box" 
                              value={startDate}
                              onChange={(e) => setStartDate(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="col-6">
                        <label className="date-label">Fecha de Fin</label>
                        <div className="date-group">
                            <input 
                              type="date" 
                              className="date-input-box" 
                              value={endDate}
                              onChange={(e) => setEndDate(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                <select 
                  className="selecter mb-4" 
                  value={criterion} 
                  onChange={(e) => setCriterion(e.target.value)}
                >
                    <option value="most">Mas Vendidos</option>
                    <option value="least">Menos Vendidos</option>
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
                            {loading ? (
                              <tr><td colSpan="2" className="text-center">Cargando...</td></tr>
                            ) : error ? (
                              <tr><td colSpan="2" className="text-center text-danger">{error}</td></tr>
                            ) : productData.length > 0 ? (
                              productData.map((item, index) => (
                                <tr key={item.product__id || index}>
                                  <td>{item.product_name} (<small>{item.units_sold} uds</small>)</td>
                                  <td>${parseFloat(item.revenue).toFixed(2)}</td>
                                </tr>
                              ))
                            ) : (
                              <tr><td colSpan="2" className="text-center">No hay datos para este periodo</td></tr>
                            )}
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
