import { useEffect, useRef } from 'react';
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

  useEffect(() => {
    if (chartRef.current) {
      const ctx = chartRef.current.getContext('2d');

      // Destroy previous chart instance if it exists
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      // Create new chart
      chartInstance.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
          datasets: [
            {
              label: 'Dataset 1',
              data: [150, 800, 450, 350, 900, 650, 480, 850, 800, 400],
              borderColor: '#E74C3C',
              backgroundColor: 'transparent',
              pointBackgroundColor: 'white',
              pointBorderColor: '#E74C3C',
              borderWidth: 1,
              tension: 0
            },
            {
              label: 'Dataset 2',
              data: [500, 950, 10, 150, 500, 750, 480, 780, 380, 950],
              borderColor: '#F39C12',
              backgroundColor: 'transparent',
              pointBackgroundColor: 'white',
              pointBorderColor: '#F39C12',
              borderWidth: 1,
              tension: 0
            },
            {
              label: 'Dataset 3',
              data: [500, 510, 450, 600, 80, 250, 280, 420, 950, 350],
              borderColor: '#3498DB',
              backgroundColor: 'transparent',
              pointBackgroundColor: 'white',
              pointBorderColor: '#3498DB',
              borderWidth: 1,
              tension: 0
            },
            {
              label: 'Dataset 4',
              data: [10, 700, 880, 550, 480, 420, 720, 980, 80, 250],
              borderColor: '#BDF589',
              backgroundColor: 'transparent',
              pointBackgroundColor: 'white',
              pointBorderColor: '#BDF589',
              borderWidth: 1,
              tension: 0
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 1000,
              ticks: {
                stepSize: 250
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
  }, []);

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
                  <tr><td></td><td></td></tr>
                  <tr><td></td><td></td></tr>
                  <tr><td></td><td></td></tr>
                  <tr><td></td><td></td></tr>
                  <tr><td></td><td></td></tr>
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
