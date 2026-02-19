import { useState, useEffect } from "react";
import Navbar from "../components/layout/Navbar";
import SearchBar from "../components/layout/SearchBar";
import ActionButtons from "../components/common/ActionButtons"; // Using for Trash Icon
import LoadingModal from "../components/common/LoadingModal";
import "../styles/Ventas.css";
import "../styles/General.css";

const Ventas = () => {
  // UI State
  const [searchTerm, setSearchTerm] = useState("");
  const [showPayModal, setShowPayModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showCardModal, setShowCardModal] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showLoadingModal, setShowLoadingModal] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [error, setError] = useState("");

  // Data State
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cart & Order State
  const [cart, setCart] = useState([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [createdOrder, setCreatedOrder] = useState(null); // Stores the order response from backend

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("No hay sesión activa");
      setLoading(false);
      return;
    }

    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [prodRes, custRes] = await Promise.all([
        fetch("/api/products/", { headers }),
        fetch("/api/customers/", { headers }),
      ]);

      if (prodRes.ok) {
        const prodData = await prodRes.json();
        setProducts(Array.isArray(prodData) ? prodData : []);
      }
      if (custRes.ok) {
        const custData = await custRes.json();
        setCustomers(Array.isArray(custData) ? custData : []);
      }
    } catch (err) {
      console.error("Error loading sales data:", err);
      setError("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  // --- Cart Logic ---
  const addToCart = (product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  };

  const removeFromCart = (productId) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const updateQuantity = (productId, delta) => {
    setCart((prev) =>
      prev.map((item) => {
        if (item.product.id === productId) {
          const newQty = Math.max(1, item.quantity + delta);
          return { ...item, quantity: newQty };
        }
        return item;
      }),
    );
  };

  const calculateLocalTotal = () => {
    return cart.reduce((sum, item) => {
      return (
        sum +
        parseFloat(item.product.final_price || item.product.price) *
          item.quantity
      );
    }, 0);
  };

  // --- Order Creation ---
  const handleInitiatePayment = async () => {
    if (cart.length === 0) {
      alert("El carrito está vacío");
      return;
    }

    setShowLoadingModal(true);
    const token = localStorage.getItem("access_token");

    // Construct payload per backend requirement
    const orderPayload = {
      customer: selectedCustomerId || null,
      items: cart.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
      })),
    };

    try {
      const response = await fetch("/api/orders/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(orderPayload),
      });

      const data = await response.json();

      if (response.ok) {
        setCreatedOrder(data); // Save the order details (ID, final amounts)
        setShowLoadingModal(false);
        setShowPayModal(true); // Open payment method selection
      } else {
        setShowLoadingModal(false);
        console.error("Order creation failed:", data);
        let msg = "Error al crear la orden";
        if (data.non_field_errors) msg = data.non_field_errors.join("\n");
        else if (data.detail) msg = data.detail;
        alert(msg);
      }
    } catch (err) {
      setShowLoadingModal(false);
      console.error("Network error creating order:", err);
      alert("Error de conexión al crear orden");
    }
  };

  // --- Payment Processing ---
  const handleProcessPayment = async (method) => {
    if (!createdOrder) return;

    setShowPayModal(false);
    setShowCashModal(false);
    setShowCardModal(false);
    setShowCreditModal(false);
    setShowLoadingModal(true);

    const token = localStorage.getItem("access_token");

    try {
      const response = await fetch(`/api/orders/${createdOrder.id}/pay/`, {
        method: "POST", // Backend doc says POST for /pay/
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ payment_method: method }),
      });

      const data = await response.json();

      if (response.ok) {
        alert("Pago procesado correctamente. Venta finalizada.");
        // Reset Logic
        setCart([]);
        setCreatedOrder(null);
        setSelectedCustomerId("");
        setPaymentAmount("");
      } else {
        console.error("Payment failed:", data);
        let msg = "Error al procesar el pago";
        if (data.detail) msg = data.detail;
        alert(msg);
      }
    } catch (err) {
      console.error("Payment network error:", err);
      alert("Error de conexión al pagar");
    } finally {
      setShowLoadingModal(false);
    }
  };

  const filteredProducts = products.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <>
      <Navbar activeItem="Ventas" />

      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar
            placeholder="Buscar Producto (Nombre o SKU)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="Gp">
          <div className="row flscn">
            {/* Left Column: Cart & Customer */}
            <div className="Client_Container col-8">
              <div className="d-flex flex-column h-100 gap-3">
                {/* Cliente Selector */}
                <div className="Client_bar">
                  <select
                    name="Client"
                    id="Client"
                    className="form-select w-50"
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(e.target.value)}
                  >
                    <option value="">Cliente Visitante</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.first_name} {c.last_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Product List */}
                <div className="Product_List_Container flex-grow-1">
                  <div className="Product_List h-100">
                    {loading ? (
                      <p className="text-center">Cargando productos...</p>
                    ) : (
                      <div className="row g-2">
                        {filteredProducts.map((product) => (
                          <div className="col-12" key={product.id}>
                            <div
                              className="card h-100 p-2 product-card"
                              style={{
                                cursor: "pointer",
                                border: "1px solid #ddd",
                              }}
                              onClick={() => addToCart(product)}
                            >
                              <div className="d-flex justify-content-between">
                                <strong>{product.name}</strong>
                                <span className="text-success fw-bold">
                                  $
                                  {parseFloat(
                                    product.final_price || product.price,
                                  ).toFixed(2)}
                                </span>
                              </div>
                              <small className="text-muted">
                                Stock:{" "}
                                {product.available_to_sell ?? product.current_stock}
                              </small>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Product Selector */}
            <div className="Product_Container col-4">
              <div className="Cart_Container">
                {/* Cart Items List */}
                <div className="Cart_List">
                  {cart.length === 0 ? (
                    <p className="text-center text-muted mt-5">Carrito Vacío</p>
                  ) : (
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Producto</th>
                          <th>Cant.</th>
                          <th>Precio</th>
                          <th>Total</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {cart.map((item) => (
                          <tr key={item.product.id}>
                            <td>{item.product.name}</td>
                            <td>
                              <button
                                className="btn btn-sm btn-outline-secondary me-1 sm-btn"
                                onClick={() => updateQuantity(item.product.id, -1)}
                              >
                                -
                              </button>
                              {item.quantity}
                              <button
                                className="btn btn-sm btn-outline-secondary ms-1 sm-btn"
                                onClick={() => updateQuantity(item.product.id, 1)}
                              >
                                +
                              </button>
                            </td>
                            <td>
                              $
                              {parseFloat(
                                item.product.final_price || item.product.price,
                              ).toFixed(2)}
                            </td>
                            <td>
                              $
                              {(
                                parseFloat(
                                  item.product.final_price || item.product.price,
                                ) * item.quantity
                              ).toFixed(2)}
                            </td>
                            <td>
                              <button
                                className="btn btn-danger md-btn"
                                onClick={() => removeFromCart(item.product.id)}
                              >
                                <i className="bi bi-trash"></i>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
                {/* Totals Area */}
                <div className="Cart_Total">
                  <h3>Total Estimado: ${calculateLocalTotal().toFixed(2)}</h3>
                </div>
              </div>
              {/* Pay Button */}
              <button
                className="button_add w-100 mt-3"
                onClick={handleInitiatePayment}
                disabled={cart.length === 0}
              >
                <i className="bi bi-currency-dollar"></i> Cobrar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pay Method Selection Modal */}
      <div
        className={`modal fade ${showPayModal ? "show" : ""}`}
        style={{
          display: showPayModal ? "block" : "none",
          backgroundColor: "rgba(0,0,0,0.5)",
        }}
        tabIndex="-1"
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-4">
                Total a Pagar: $
                {createdOrder ? createdOrder.final_amount : "0.00"}
              </h2>
              <h5 className="text-center mb-5 text-muted">
                Seleccione Método de Pago
              </h5>

              <div className="row text-center justify-content-center g-3">
                <div className="col-4">
                  <button
                    className="Invs_btn w-100"
                    onClick={() => {
                      setShowPayModal(false);
                      setShowCashModal(true);
                    }}
                  >
                    <i className="bi bi-cash-coin fs-1"></i>
                    <h4>Efectivo</h4>
                  </button>
                </div>
                <div className="col-4">
                  <button
                    className="Invs_btn w-100"
                    onClick={() => handleProcessPayment("CARD")}
                  >
                    <i className="bi bi-credit-card fs-1"></i>
                    <h4>Tarjeta</h4>
                  </button>
                </div>
                {/* Only show credit/points if customer is selected, optionally */}
                <div className="col-4">
                  <button
                    className="Invs_btn w-100"
                    onClick={() => handleProcessPayment("CREDIT")}
                  >
                    <i className="bi bi-bank fs-1"></i>
                    <h4>Crédito</h4>
                  </button>
                </div>
              </div>
              <div className="row mt-3">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowPayModal(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cash Payment Modal */}
      <div
        className={`modal fade ${showCashModal ? "show" : ""}`}
        style={{
          display: showCashModal ? "block" : "none",
          backgroundColor: "rgba(0,0,0,0.5)",
        }}
        tabIndex="-1"
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center">Pago en Efectivo</h2>
              <h3 className="text-center Text_Total my-4">
                Total: ${createdOrder ? createdOrder.final_amount : "0.00"}
              </h3>

              <form
                className="text-center"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleProcessPayment("CASH");
                }}
              >
                <h5>Monto Recibido</h5>
                <input
                  type="number"
                  className="form-control mb-3 text-center"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  placeholder="0.00"
                />

                {paymentAmount &&
                  createdOrder &&
                  parseFloat(paymentAmount) >=
                    parseFloat(createdOrder.final_amount) && (
                    <div className="alert alert-success">
                      Cambio: $
                      {(
                        parseFloat(paymentAmount) -
                        parseFloat(createdOrder.final_amount)
                      ).toFixed(2)}
                    </div>
                  )}

                <div className="d-grid gap-2">
                  <button
                    type="submit"
                    className="btn btn-success btn-lg"
                    disabled={
                      !paymentAmount ||
                      parseFloat(paymentAmount) <
                        parseFloat(createdOrder?.final_amount || 0)
                    }
                  >
                    Confirmar Pago
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowCashModal(false)}
                  >
                    Regresar
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Loading Modal */}
      <LoadingModal show={showLoadingModal} onHide={() => {}} />
    </>
  );
};

export default Ventas;
