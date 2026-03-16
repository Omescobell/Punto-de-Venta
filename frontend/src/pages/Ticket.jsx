import React, { useEffect } from 'react';
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import "../styles/General.css";
import "../styles/Ticket.css";

const Ticket = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Datos de prueba para previsualización
  const dummyData = {
    order: { id: "123456", final_amount: 1550.50, customer_name: "Juan Pérez" },
    items: [
      { product: { name: "Producto de Ejemplo A", price: 500.00, final_price: 450.00 }, quantity: 2 },
      { product: { name: "Producto de Ejemplo B", price: 650.00 }, quantity: 1 }
    ],
    paymentMethod: "CASH",
    paymentAmount: 2000.00
  };

  const stateData = location.state || {};
  const order = stateData.order || dummyData.order;
  const items = stateData.items || dummyData.items;
  const paymentMethod = stateData.paymentMethod || dummyData.paymentMethod;
  const paymentAmount = stateData.paymentAmount || dummyData.paymentAmount;

  useEffect(() => {
    if (order && items) {
      // Small delay to ensure styles and data are loaded
      const timer = setTimeout(() => {
        window.print();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [order, items]);

  if (!order || !items) {
    return (
      <>
        <Navbar activeItem="Ventas" />
        <div className="Main-Container text-center mt-5">
          <h2>No hay datos de venta disponibles</h2>
          <button className="btn btn-primary mt-3" onClick={() => navigate("/ventas")}>
            Ir a Ventas
          </button>
        </div>
      </>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <>
      <Navbar activeItem="Ventas" />
      <div className="Main-Container">
        <div className="container mt-4 mb-5" style={{ maxWidth: "800px" }}>
          <div className="card shadow-sm p-4 ticket-card">
            <div className="text-center mb-4">
              <h1 className="fw-bold">TICKET DE VENTA</h1>
              <p className="text-muted">Orden #{order.id}</p>
              <hr />
            </div>

            <div className="row mb-3">
              <div className="col-6">
                <strong>Fecha:</strong> {new Date().toLocaleString()}
              </div>
              <div className="col-6 text-end">
                <strong>Cliente:</strong> {order.customer_name || "Cliente Visitante"}
              </div>
            </div>

            <table className="table table-striped mt-3">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th className="text-center">Cant.</th>
                  <th className="text-end">P. Unitario</th>
                  <th className="text-end">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr key={index}>
                    <td>{item.product.name}</td>
                    <td className="text-center">{item.quantity}</td>
                    <td className="text-end">
                      ${parseFloat(item.product.final_price || item.product.price).toFixed(2)}
                    </td>
                    <td className="text-end">
                      $
                      {(
                        parseFloat(item.product.final_price || item.product.price) *
                        item.quantity
                      ).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="row mt-4">
              <div className="col-7">
                <p><strong>Método de Pago:</strong> {paymentMethod === 'CASH' ? 'Efectivo' : paymentMethod === 'CARD' ? 'Tarjeta' : 'Crédito'}</p>
                {paymentMethod === 'CASH' && paymentAmount && (
                  <>
                    <p><strong>Recibido:</strong> ${parseFloat(paymentAmount).toFixed(2)}</p>
                    <p><strong>Cambio:</strong> ${(parseFloat(paymentAmount) - parseFloat(order.final_amount)).toFixed(2)}</p>
                  </>
                )}
              </div>
              <div className="col-5 text-end">
                <h3 className="fw-bold">TOTAL: ${parseFloat(order.final_amount).toFixed(2)}</h3>
              </div>
            </div>

            <div className="d-flex justify-content-between mt-5 no-print">
              <button className="btn btn-secondary" onClick={() => navigate("/ventas")}>
                Nueva Venta
              </button>
              <button className="btn btn-primary" onClick={handlePrint}>
                <i className="bi bi-printer me-2"></i>Imprimir Ticket
              </button>
            </div>
          </div>
        </div>
      </div>

      
    </>
  );
};

export default Ticket;