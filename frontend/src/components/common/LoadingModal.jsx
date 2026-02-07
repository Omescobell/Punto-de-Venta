import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

const LoadingModal = ({ show, onHide }) => {
  const [showLoading, setShowLoading] = useState(true);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (show) {
      // Reset states
      setShowLoading(true);
      setShowSuccess(false);

      // After 3 seconds, show checkmark
      const loadingTimer = setTimeout(() => {
        setShowLoading(false);
        setShowSuccess(true);

        // Close modal after 2 more seconds
        const successTimer = setTimeout(() => {
          if (onHide) onHide();
        }, 2000);

        return () => clearTimeout(successTimer);
      }, 3000);

      return () => clearTimeout(loadingTimer);
    }
  }, [show, onHide]);

  if (!show) return null;

  return (
    <div className={`modal fade ${show ? 'show' : ''}`} 
         style={{ display: show ? 'block' : 'none' }}
         tabIndex="-1" 
         aria-hidden={!show}
         data-bs-backdrop="static" 
         data-bs-keyboard="false">
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content loading-modal-content">
          <div className="modal-body text-center">
            {/* Loading State */}
            <div id="loadingState" 
                 className="loading-state" 
                 style={{ display: showLoading ? 'block' : 'none' }}>
              <div className="spinner-border text-primary" 
                   role="status" 
                   style={{ width: '4rem', height: '4rem' }}>
                <span className="visually-hidden">Cargando...</span>
              </div>
              <h4 className="mt-4">Procesando pago...</h4>
            </div>
            
            {/* Success State */}
            <div id="successState" 
                 className="success-state" 
                 style={{ display: showSuccess ? 'block' : 'none' }}>
              <div className="checkmark-circle">
                <svg className="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                  <circle className="checkmark-circle-path" cx="26" cy="26" r="25" fill="none"/>
                  <path className="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
              </div>
              <h4 className="mt-4 success-text">Pago correcto</h4>
            </div>
          </div>
        </div>
      </div>
      {show && <div className="modal-backdrop fade show"></div>}
    </div>
  );
};

LoadingModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func
};

export default LoadingModal;
