import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import SearchBar from "../components/layout/SearchBar";
import ActionButtons from "../components/common/ActionButtons"; // Using for Trash Icon
import LoadingModal from "../components/common/LoadingModal";
// We leave Ventas.css just for the Custom SVG animations used by LoadingModal inside it
import "../styles/Ventas.css";

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

  const navigate = useNavigate();

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
        setSelectedCustomerId("");
        setPaymentAmount("");

        // Navigate to Ticket
        navigate("/ticket", {
          state: {
            order: data.order || createdOrder, // Depending on backend response structure
            items: cart,
            paymentMethod: method,
            paymentAmount: paymentAmount,
          },
        });
        setCart([]);
        setCreatedOrder(null);
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

      <div className="flex flex-col w-full px-[5%] pb-[5%]">
        <div className="flex flex-row items-center justify-center gap-[20px] mb-[30px] w-full">
          <SearchBar
            placeholder="Buscar Producto (Nombre o SKU)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div>
          <div className="flex flex-col lg:flex-row justify-between h-[80vh] w-full gap-5">
            {/* Left Column: Cart & Customer */}
            <div className="w-full lg:w-2/3 flex flex-col h-full p-2.5">
              <div className="flex flex-col h-full gap-3">
                {/* Cliente Selector */}
                <div className="bg-white w-full rounded-xl p-2.5 flex items-center justify-center flex-row shadow-sm">
                  <select
                    name="Client"
                    id="Client"
                    className="w-[50%] p-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                <div className="bg-white w-full flex-grow overflow-y-auto rounded-xl p-2.5 shadow-sm">
                  <div className="bg-white h-full w-full rounded-xl p-2.5 text-[#666]">
                    {loading ? (
                      <p className="text-center text-gray-500">Cargando productos...</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredProducts.map((product) => (
                          <div className="col-span-1" key={product.id}>
                            <div
                              className="bg-white rounded-xl p-4 border border-[#ddd] cursor-pointer hover:shadow-md transition-shadow h-full flex flex-col justify-center"
                              onClick={() => addToCart(product)}
                            >
                              <div className="flex flex-row justify-between items-center mb-1">
                                <strong className="text-gray-800 text-lg line-clamp-1" title={product.name}>{product.name}</strong>
                                <span className="text-[#1eb35b] font-bold text-lg whitespace-nowrap">
                                  $
                                  {parseFloat(
                                    product.final_price || product.price,
                                  ).toFixed(2)}
                                </span>
                              </div>
                              <small className="text-gray-500">
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
            <div className="w-full lg:w-1/3 bg-[#f9f9f9] border-l border-[#eee] flex flex-col h-full p-4 rounded-xl shadow-sm">
              <div className="flex flex-col flex-grow overflow-hidden border border-[#ddd] rounded-xl bg-white">
                {/* Cart Items List */}
                <div className="flex-1 overflow-y-auto p-2.5 bg-white rounded-t-xl">
                  {cart.length === 0 ? (
                    <p className="text-center text-gray-400 mt-10">Carrito Vacío</p>
                  ) : (
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="p-2 font-medium text-gray-600">Producto</th>
                          <th className="p-2 font-medium text-gray-600 text-center">Cant.</th>
                          <th className="p-2 font-medium text-gray-600 text-right">Total</th>
                          <th className="p-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {cart.map((item) => (
                          <tr key={item.product.id} className="border-b border-gray-100 last:border-none">
                            <td className="p-2 text-gray-800 font-medium">
                              {item.product.name}
                              <div className="text-sm text-gray-500">${parseFloat(item.product.final_price || item.product.price).toFixed(2)} c/u</div>
                            </td>
                            <td className="p-2">
                              <div className="flex items-center justify-center gap-2">
                                <button
                                  className="w-[30px] h-[30px] rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors"
                                  onClick={() => updateQuantity(item.product.id, -1)}
                                >
                                  -
                                </button>
                                <span className="w-6 text-center">{item.quantity}</span>
                                <button
                                  className="w-[30px] h-[30px] rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors"
                                  onClick={() => updateQuantity(item.product.id, 1)}
                                >
                                  +
                                </button>
                              </div>
                            </td>
                            <td className="p-2 text-right text-gray-800 font-semibold">
                              $
                              {(
                                parseFloat(
                                  item.product.final_price || item.product.price,
                                ) * item.quantity
                              ).toFixed(2)}
                            </td>
                            <td className="p-2 text-right">
                              <button
                                className="w-[40px] h-[40px] bg-red-500 text-white rounded-lg flex justify-center items-center hover:bg-red-600 transition-colors shadow-sm"
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
                <div className="p-4 bg-[#f0f0f0] border-t border-[#ddd] rounded-b-xl flex justify-between items-center">
                  <h3 className="m-0 text-xl font-bold text-gray-800">Total Estimado:</h3>
                  <h3 className="m-0 text-xl font-bold text-[#1eb35b]">${calculateLocalTotal().toFixed(2)}</h3>
                </div>
              </div>
              {/* Pay Button */}
              <button
                className="bg-[#1eb35b] text-white border-none rounded-xl p-4 text-[1.8rem] w-full flex items-center justify-center gap-2.5 transition-transform hover:scale-[1.02] hover:bg-[#17964b] mt-4 shadow-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleInitiatePayment}
                disabled={cart.length === 0}
              >
                <i className="bi bi-currency-dollar text-[2.2rem]"></i> Cobrar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pay Method Selection Modal */}
      {showPayModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 transition-opacity" tabIndex="-1">
          <div className="w-[500px] max-w-[90%] mx-auto relative bg-[#a8a8a8] rounded-xl p-8 shadow-2xl">
            <h2 className="text-center font-bold text-gray-800 text-3xl mb-4">
              Total a Pagar: ${createdOrder ? createdOrder.final_amount : "0.00"}
            </h2>
            <h5 className="text-center mb-8 text-gray-600 text-lg">
              Seleccione Método de Pago
            </h5>

            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-1">
                <button
                  className="bg-transparent border-none p-4 w-full cursor-pointer transition-all text-[#444] hover:scale-110 hover:text-[#1eb35b] flex flex-col items-center justify-center group"
                  onClick={() => {
                    setShowPayModal(false);
                    setShowCashModal(true);
                  }}
                >
                  <i className="bi bi-cash-coin text-[4rem] mb-2 group-hover:text-[#1eb35b]"></i>
                  <h4 className="font-medium text-lg m-0">Efectivo</h4>
                </button>
              </div>
              <div className="col-span-1">
                <button
                  className="bg-transparent border-none p-4 w-full cursor-pointer transition-all text-[#444] hover:scale-110 hover:text-[#1eb35b] flex flex-col items-center justify-center group"
                  onClick={() => handleProcessPayment("CARD")}
                >
                  <i className="bi bi-credit-card text-[4rem] mb-2 group-hover:text-[#1eb35b]"></i>
                  <h4 className="font-medium text-lg m-0">Tarjeta</h4>
                </button>
              </div>
              <div className="col-span-1">
                <button
                  className="bg-transparent border-none p-4 w-full cursor-pointer transition-all text-[#444] hover:scale-110 hover:text-[#1eb35b] flex flex-col items-center justify-center group"
                  onClick={() => handleProcessPayment("CREDIT")}
                >
                  <i className="bi bi-bank text-[4rem] mb-2 group-hover:text-[#1eb35b]"></i>
                  <h4 className="font-medium text-lg m-0">Crédito</h4>
                </button>
              </div>
            </div>
            <div className="flex justify-center mt-6">
              <button
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
                onClick={() => setShowPayModal(false)}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cash Payment Modal */}
      {showCashModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 transition-opacity" tabIndex="-1">
          <div className="w-[450px] max-w-[90%] mx-auto relative bg-[#a8a8a8] rounded-xl p-8 shadow-2xl">
            <h2 className="text-center font-bold text-gray-800 text-3xl mb-4">Pago en Efectivo</h2>
            <h3 className="text-center font-medium text-[#555] text-2xl my-6">
              Total: ${createdOrder ? createdOrder.final_amount : "0.00"}
            </h3>

            <form
              className="text-center"
              onSubmit={(e) => {
                e.preventDefault();
                handleProcessPayment("CASH");
              }}
            >
              <h5 className="text-gray-700 font-medium mb-2">Monto Recibido</h5>
              <input
                type="number"
                className="w-[80%] mx-auto block rounded-lg border border-gray-300 bg-white p-3 text-center text-xl focus:outline-none focus:ring-2 focus:ring-blue-500 mb-6"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder="0.00"
              />

              {paymentAmount &&
                createdOrder &&
                parseFloat(paymentAmount) >=
                  parseFloat(createdOrder.final_amount) && (
                  <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-6 text-lg font-medium">
                    Cambio: $
                    {(
                      parseFloat(paymentAmount) -
                      parseFloat(createdOrder.final_amount)
                    ).toFixed(2)}
                  </div>
                )}

              <div className="flex flex-col gap-3">
                <button
                  type="submit"
                  className="w-full bg-[#1eb35b] text-white font-bold py-3 text-xl rounded-lg hover:bg-[#17964b] transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
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
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 text-xl rounded-lg transition-colors shadow-md"
                  onClick={() => setShowCashModal(false)}
                >
                  Regresar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loading Modal */}
      <LoadingModal show={showLoadingModal} onHide={() => {}} />
    </>
  );
};

export default Ventas;
