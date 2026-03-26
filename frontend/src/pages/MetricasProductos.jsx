import { useEffect, useRef, useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SubHeader from '../components/layout/SubHeader';
import { Chart } from 'chart.js/auto'; // Import Chart.js

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
    <div className="min-h-screen bg-[#F5F5F5]">
      <Navbar activeItem="Métricas" />
      <SubHeader items={subHeaderItems} activeItem="Productos" />

      <div className="px-[5%] pb-[50px]">
        {/* Título Periodo */}
        <div className="w-full">
            <h1 className="text-[48px] font-bold mb-[20px] text-[#1a1a1a]">Periodo</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Columna Izquierda: Inputs y Tabla */}
            <div className="md:col-span-5 lg:col-span-4">
                
                {/* Inputs de Fecha */}
                <div className="flex flex-row justify-between gap-4 mb-10 w-full">
                    <div className="flex-1">
                        <label className="text-[14px] text-[#555] mb-[5px] block font-medium">Fecha de inicio</label>
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
                        <label className="text-[14px] text-[#555] mb-[5px] block font-medium">Fecha de Fin</label>
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

                <select 
                  className="w-full h-12 bg-white border border-[#ddd] rounded-lg p-2 text-center text-[15px] outline-none focus:ring-2 focus:ring-blue-400 font-medium mb-8 shadow-sm cursor-pointer text-black" 
                  value={criterion} 
                  onChange={(e) => setCriterion(e.target.value)}
                >
                    <option value="most">Más Vendidos</option>
                    <option value="least">Menos Vendidos</option>
                </select>
                
                {/* Tabla */}
                <div className="mt-8 overflow-x-auto">
                    <table className="w-full border-collapse border border-[#888] shadow-sm">
                        <thead>
                            <tr>
                                <th className="bg-[#EAEAEA] p-[15px] text-left text-[18px] sm:text-[22px] font-bold border border-[#888] w-[50%]">Producto</th>
                                <th className="bg-[#EAEAEA] p-[15px] text-left text-[18px] sm:text-[22px] font-bold border border-[#888] w-[50%]">Total de Ingresos</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                              <tr><td colSpan="2" className="text-center bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium">Cargando...</td></tr>
                            ) : error ? (
                              <tr><td colSpan="2" className="text-center text-red-600 bg-[#EAEAEA] h-[50px] border border-[#888] px-4 font-medium">{error}</td></tr>
                            ) : productData.length > 0 ? (
                              productData.map((item, index) => (
                                <tr key={item.product__id || index} className="hover:bg-gray-50">
                                  <td className="bg-white h-[50px] border border-[#888] px-4 py-2 font-medium text-gray-800">
                                    {item.product_name} <br/><span className="text-gray-500 text-sm font-normal">({item.units_sold} unidades)</span>
                                  </td>
                                  <td className="bg-white h-[50px] border border-[#888] px-4 font-medium text-gray-800">
                                    ${parseFloat(item.revenue).toFixed(2)}
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

            {/* Columna Derecha: Gráfica */}
            <div className="md:col-span-7 lg:col-span-8">
                <div className="relative h-[400px] w-full mt-5 md:mt-0 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <canvas ref={chartRef}></canvas>
                </div>
            </div>
        </div>
    </div>
    </div>
  );
};

export default MetricasProductos;
