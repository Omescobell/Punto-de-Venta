import { useEffect, useRef, useState } from 'react';
import { Chart, registerables } from 'chart.js';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import '../styles/Metricas-Ventas.css';

// Register Chart.js components
Chart.register(...registerables);

const Metricas = () => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  const subHeaderItems = [
    { name: 'Ventas', path: '/metricas' },
    { name: 'Productos', path: '/metricas-productos' }
  ];

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [salesData, setSalesData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSalesData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      let url = '/api/analytics/sales-summary/';
      const params = new URLSearchParams();
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
        let errorMsg = 'Error al cargar métricas de ventas';
        try {
          const errData = await response.json();
          if (errData.error) errorMsg = errData.error;
          else if (typeof errData === 'string') errorMsg = errData;
        } catch (e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setSalesData(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSalesData();
  }, [startDate, endDate]);

  useEffect(() => {
    if (chartRef.current && salesData?.peak_hours?.hourly_breakdown) {
      const ctx = chartRef.current.getContext('2d');

      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const breakdown = salesData.peak_hours.hourly_breakdown;
      // Sort by hour if needed
      const sortedBreakdown = [...breakdown].sort((a, b) => a.hour - b.hour);
      
      const labels = sortedBreakdown.map(item => `${item.hour}:00`);
      const revenueData = sortedBreakdown.map(item => parseFloat(item.total_revenue));

      chartInstance.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Ventas (Ingresos)',
              data: revenueData,
              borderColor: '#3498DB',
              backgroundColor: 'rgba(52, 152, 219, 0.1)',
              pointBackgroundColor: 'white',
              pointBorderColor: '#3498DB',
              borderWidth: 2,
              tension: 0.3,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'bottom'
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(context.parsed.y);
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function(value, index, values) {
                  return '$' + value;
                }
              },
              grid: {
                color: '#e0e0e0'
              }
            },
            x: {
              grid: {
                color: '#e0e0e0'
              }
            }
          },
          elements: {
            point: {
              radius: 4,
              hoverRadius: 6
            }
          }
        }
      });
    }

    // Cleanup
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [salesData]);

  return (
    <>
      <Navbar activeItem="Métricas" />
      <SubHeader items={subHeaderItems} activeItem="Ventas" />
      
      <div className="Main-Container">
        <div className="row">
          <div className="col-12">
            <h1 className="periodo-title">Periodo</h1>
          </div>
        </div>

        <div className="row">
          {/* Left Column: Date Inputs and Table */}
          <div className="col-md-5 col-lg-4">
            {/* Date Inputs */}
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

            {/* Table */}
            <div className="tabla-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Ventas</th>
                    <th>Dinero</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan="2" className="text-center">Cargando...</td></tr>
                  ) : error ? (
                    <tr><td colSpan="2" className="text-center text-danger">{error}</td></tr>
                  ) : salesData?.payment_methods?.length > 0 ? (
                    salesData.payment_methods.map((method, index) => (
                      <tr key={index}>
                        <td>{method.payment_method === 'CASH' ? 'Efectivo' : method.payment_method === 'CARD' ? 'Tarjeta' : method.payment_method === 'TRANSFER' ? 'Transferencia' : method.payment_method} ({method.total_sales})</td>
                        <td>${parseFloat(method.accumulated_amount).toFixed(2)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="2" className="text-center">No hay datos para este periodo</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Chart */}
          <div className="col-md-7 col-lg-8">
            <div className="chart-container">
              <canvas ref={chartRef} id="salesChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Metricas;
