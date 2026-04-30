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

  const handleSendTelegram = async () => {
    // Solo necesitamos el Token del Bot desde el .env
    const botToken = import.meta.env.VITE_TELEGRAM_BOT_TOKEN;

    if (!botToken) {
      alert("Por favor, configura tu Bot Token de Telegram en tu archivo .env (VITE_TELEGRAM_BOT_TOKEN).");
      return;
    }

    // Preguntamos al cajero el ID del cliente
    const customerChatId = window.prompt(
      "Ingresa el Chat ID de Telegram del cliente para enviarle su ticket:\n\n(El cliente puede obtenerlo desde Telegram enviando un mensaje al bot @getmyid_bot)"
    );

    // Si el cajero cancela o lo deja vacío, detenemos el envío
    if (!customerChatId || customerChatId.trim() === "") {
      return;
    }

    const text = `🧾 *TICKET DE VENTA*
*Orden:* #${order.id}
*Fecha:* ${new Date().toLocaleString()}
*Cliente:* ${order.customer_name || "Cliente Visitante"}
-----------------------------------
${items.map(i => `${i.quantity}x ${i.product.name} - $${(parseFloat(i.product.final_price || i.product.price) * i.quantity).toFixed(2)}`).join('\n')}
-----------------------------------
*Total:* $${parseFloat(order.final_amount).toFixed(2)}
*Método:* ${paymentMethod === 'CASH' ? 'Efectivo' : paymentMethod === 'CARD' ? 'Tarjeta' : 'Crédito'}`;

    try {
      const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: customerChatId.trim(),
          text: text,
          parse_mode: "Markdown"
        })
      });

      if (response.ok) {
        alert("Ticket enviado exitosamente por Telegram al cliente.");
      } else {
        const data = await response.json();
        console.error("Error de Telegram:", data);
        alert(`Hubo un error al enviar el ticket: ${data.description || 'Verifica que el Chat ID sea correcto y que el cliente haya iniciado chat con el bot.'}`);
      }
    } catch (error) {
      console.error("Error de red:", error);
      alert("Error de conexión al intentar enviar el ticket.");
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
                <button className="btn btn-info text-white" onClick={handleSendTelegram}>
                  <i className="bi bi-telegram me-2"></i>Enviar Telegram
                </button>
                <button className="btn btn-primary" onClick={handlePrint}>
                  <i className="bi bi-printer me-2"></i>Imprimir Ticket
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      
    </>
  );
};

export default Ticket;