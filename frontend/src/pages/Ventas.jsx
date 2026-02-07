import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import SearchBar from '../components/layout/SearchBar';
import ActionButtons from '../components/common/ActionButtons';
import LoadingModal from '../components/common/LoadingModal';
import '../styles/Ventas.css';
import '../styles/General.css';

const Ventas = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showPayModal, setShowPayModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showCardModal, setShowCardModal] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showLoadingModal, setShowLoadingModal] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');

  const handleFinalizarPago = () => {
    setShowCashModal(false);
    setShowLoadingModal(true);
  };

  const handleCreditPago = () => {
    setShowCreditModal(false);
    setShowLoadingModal(true);
  };

  return (
    <>
      <Navbar activeItem="Ventas" />
      
      <div className="Main-Container">
        <div className="Tools_Container">
          <SearchBar 
            placeholder="Buscar Proveedor"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="Gp">
          <div className="row">
          <div className="Client_Container col-8">
            <select name="Client" id="Client">
              <option value="">Seleccione Cliente</option>
              <option value="">Cliente 1</option>
              <option value="">Cliente 2</option>
            </select>
            <p>Puntos del cliente:</p>
            <p>0</p>
            <p>pts.</p>
          </div>
          <div className="Product_Container col-4">
            <div className="Product_List">
              {/* Products will be listed here */}
            </div>
            <button 
              className="button_add" 
              onClick={() => setShowPayModal(true)}
            >
              <i className="bi bi-plus-lg"> Pagar</i>
            </button>
          </div>
          </div>
        </div>
      </div>

      {/* Pay Modal */}
      <div className={`modal fade ${showPayModal ? 'show' : ''}`} 
           style={{ display: showPayModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content Custom-Modal-Style">
            <div className="modal-body">
              <h2 className="text-center mb-5">Método de Pago</h2>
              <div className="row text-center justify-content-center">
                <div className="col-4">
                  <button 
                    className="Invs_btn" 
                    onClick={() => {
                      setShowPayModal(false);
                      setShowCashModal(true);
                    }}
                  >
                    <i className="bi bi-currency-dollar"></i>
                    <h4>Efectivo</h4>
                  </button>
                </div>
                <div className="col-4">
                  <button 
                    className="Invs_btn"
                    onClick={() => {
                      setShowPayModal(false);
                      setShowCardModal(true);
                    }}
                  >
                    <i className="bi bi-credit-card"></i>
                    <h4>Tarjeta</h4>
                  </button>
                </div>
                <div className="col-4">
                  <button 
                    className="Invs_btn"
                    onClick={() => {
                      setShowPayModal(false);
                      setShowCreditModal(true);
                    }}
                  >
                    <i className="bi bi-bank"></i>
                    <h4>Crédito</h4>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        {showPayModal && <div className="modal-backdrop fade show" onClick={() => setShowPayModal(false)}></div>}
      </div>

      {/* Cash Modal */}
      <div className={`modal fade ${showCashModal ? 'show' : ''}`} 
           style={{ display: showCashModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-body">
              <h2 className="text-center">Pago en Efectivo</h2>
              <h3 className="text-center Text_Total" id="Total">Total: $0.00</h3>
              <form className="text-center" onSubmit={(e) => e.preventDefault()}>
                <h5>Monto Recibido</h5>
                <input 
                  type="number" 
                  className="pay_input" 
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                />
                <br />
                <button 
                  type="button" 
                  className="btn btn-success" 
                  onClick={handleFinalizarPago}
                >
                  finalizar pago
                </button>
              </form>
            </div>
          </div>
        </div>
        {showCashModal && <div className="modal-backdrop fade show" onClick={() => setShowCashModal(false)}></div>}
      </div>

      {/* Card Modal */}
      <div className={`modal fade ${showCardModal ? 'show' : ''}`} 
           style={{ display: showCardModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-body">
              <h2>Pago en Tarjeta</h2>
            </div>
          </div>
        </div>
        {showCardModal && <div className="modal-backdrop fade show" onClick={() => setShowCardModal(false)}></div>}
      </div>
      {/* Credit Modal */}
      <div className={`modal fade ${showCreditModal ? 'show' : ''}`} 
           style={{ display: showCreditModal ? 'block' : 'none' }}
           tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-body">
              <h2>Pago en Credito</h2>
            </div>
          </div>
        </div>
        {showCreditModal && <div className="modal-backdrop fade show" onClick={() => setShowCreditModal(false)}></div>}
      </div>



      {/* Loading Modal */}
      <LoadingModal 
        show={showLoadingModal} 
        onHide={() => setShowLoadingModal(false)} 
      />
    </>
  );
};

export default Ventas;
