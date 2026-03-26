import { useEffect, useRef, useState } from 'react';
import { Chart, registerables } from 'chart.js';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';

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
    <div className="min-h-screen bg-[#F5F5F5]">
      <Navbar activeItem="Métricas" />
      <SubHeader items={subHeaderItems} activeItem="Ventas" />
      
      <div className="px-[5%] pb-[50px]">
        <div className="w-full">
          <h1 className="text-[48px] font-bold mb-[20px] text-[#1a1a1a]">Periodo</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Left Column: Date Inputs and Table */}
          <div className="md:col-span-5 lg:col-span-4">
            {/* Date Inputs */}
            <div className="flex flex-row justify-between gap-4 mb-10 w-full">
              <div className="flex-1">
                <label className="text-[14px] text-[#555] mb-[5px] block font-medium text-black">Fecha de inicio</label>
                <div className="flex gap-[10px]">
                  <input 
                    type="date" 
                    className="bg-white border border-[#ddd] rounded-[5px] p-[8px] text-center w-full max-w-[160px] text-[14px] outline-none focus:ring-2 focus:ring-blue-400 text-black" 
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex-1">
                <label className="text-[14px] text-[#555] mb-[5px] block font-medium text-black">Fecha de Fin</label>
                <div className="flex gap-[10px]">
                  <input 
                    type="date" 
                    className="bg-white border border-[#ddd] rounded-[5px] p-[8px] text-center w-full max-w-[160px] text-[14px] outline-none focus:ring-2 focus:ring-blue-400 text-black" 
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="mt-10 overflow-x-auto">
              <table className="w-full border-collapse border border-[#888] shadow-sm">
                <thead>
                  <tr>
                    <th className="bg-[#EAEAEA] p-[15px] text-left text-[20px] sm:text-[24px] font-bold border border-[#888] w-[50%]">Ventas</th>
                    <th className="bg-[#EAEAEA] p-[15px] text-left text-[20px] sm:text-[24px] font-bold border border-[#888] w-[50%]">Dinero</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan="2" className="text-center bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium">Cargando...</td></tr>
                  ) : error ? (
                    <tr><td colSpan="2" className="text-center text-red-600 bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium">{error}</td></tr>
                  ) : salesData?.payment_methods?.length > 0 ? (
                    salesData.payment_methods.map((method, index) => (
                      <tr key={index}>
                        <td className="bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium text-gray-800">
                          {method.payment_method === 'CASH' ? 'Efectivo' : method.payment_method === 'CARD' ? 'Tarjeta' : method.payment_method === 'TRANSFER' ? 'Transferencia' : method.payment_method} ({method.total_sales})
                        </td>
                        <td className="bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium text-gray-800">
                          ${parseFloat(method.accumulated_amount).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="2" className="text-center bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium text-gray-500">No hay datos para este periodo</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Chart */}
          <div className="md:col-span-7 lg:col-span-8">
            <div className="relative h-[400px] w-full mt-5 md:mt-0 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
              <canvas ref={chartRef} id="salesChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Metricas;
