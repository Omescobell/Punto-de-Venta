import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import "../styles/General.css";
import "../styles/Ticket.css";

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const Ticket = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // --- Estado del modal de email ---
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailInput, setEmailInput] = useState('');
  const [emailSending, setEmailSending] = useState(false);
  const [emailStatus, setEmailStatus] = useState(null); // { type: 'success'|'error', msg: string }

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

  // --- Lógica de envío de email ---
  const openEmailModal = () => {
    setEmailInput('');
    setEmailStatus(null);
    setShowEmailModal(true);
  };

  const closeEmailModal = () => {
    setShowEmailModal(false);
    setEmailStatus(null);
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    if (!emailInput.trim()) return;

    setEmailSending(true);
    setEmailStatus(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/api/orders/${order.id}/send-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ email: emailInput.trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        setEmailStatus({ type: 'success', msg: data.detail || 'Ticket enviado exitosamente.' });
      } else {
        setEmailStatus({ type: 'error', msg: data.error || 'Hubo un error al enviar el correo.' });
      }
    } catch (err) {
      setEmailStatus({ type: 'error', msg: 'Error de conexión. Verifica tu red e inténtalo de nuevo.' });
    } finally {
      setEmailSending(false);
    }
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

            <div className="d-flex justify-content-between mt-5 no-print gap-2 flex-wrap">
              <button className="btn btn-secondary" onClick={() => navigate("/ventas")}>
                Nueva Venta
              </button>
              <div className="d-flex gap-2">
                <button className="btn btn-success text-white" onClick={openEmailModal} id="btn-enviar-email">
                  <i className="bi bi-envelope-fill me-2"></i>Enviar por Correo
                </button>
                <button className="btn btn-primary" onClick={handlePrint}>
                  <i className="bi bi-printer me-2"></i>Imprimir Ticket
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ===== Modal de Envío por Correo ===== */}
      {showEmailModal && (
        <div
          className="modal fade show d-block"
          tabIndex="-1"
          role="dialog"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={(e) => { if (e.target === e.currentTarget) closeEmailModal(); }}
        >
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content shadow-lg" style={{ borderRadius: '14px', overflow: 'hidden' }}>

              {/* Header */}
              <div className="modal-header" style={{ background: '#1a1a2e', color: '#fff', border: 'none' }}>
                <h5 className="modal-title d-flex align-items-center gap-2" id="email-modal-title">
                  <i className="bi bi-envelope-fill"></i>
                  Enviar Ticket por Correo
                </h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  aria-label="Cerrar"
                  onClick={closeEmailModal}
                  disabled={emailSending}
                ></button>
              </div>

              {/* Body */}
              <div className="modal-body p-4">
                <p className="text-muted mb-3" style={{ fontSize: '0.9rem' }}>
                  Ingresa el correo electrónico del cliente para enviarle una copia del ticket de la orden <strong>#{order.id}</strong>.
                </p>

                <form onSubmit={handleSendEmail} id="form-enviar-email">
                  <div className="mb-3">
                    <label htmlFor="email-cliente-input" className="form-label fw-semibold">
                      <i className="bi bi-at me-1"></i>Correo del cliente
                    </label>
                    <input
                      type="email"
                      id="email-cliente-input"
                      className="form-control form-control-lg"
                      placeholder="cliente@ejemplo.com"
                      value={emailInput}
                      onChange={(e) => setEmailInput(e.target.value)}
                      required
                      disabled={emailSending}
                      autoFocus
                    />
                  </div>

                  {/* Feedback de estado */}
                  {emailStatus && (
                    <div className={`alert alert-${emailStatus.type === 'success' ? 'success' : 'danger'} d-flex align-items-center gap-2 py-2`}>
                      <i className={`bi ${emailStatus.type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'}`}></i>
                      {emailStatus.msg}
                    </div>
                  )}
                </form>
              </div>

              {/* Footer */}
              <div className="modal-footer border-0 pt-0 pb-4 px-4 gap-2">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={closeEmailModal}
                  disabled={emailSending}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  form="form-enviar-email"
                  className="btn btn-success d-flex align-items-center gap-2"
                  disabled={emailSending || !emailInput.trim()}
                  id="btn-confirmar-envio-email"
                >
                  {emailSending ? (
                    <>
                      <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                      Enviando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-send-fill"></i>
                      Enviar Ticket
                    </>
                  )}
                </button>
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Ticket;