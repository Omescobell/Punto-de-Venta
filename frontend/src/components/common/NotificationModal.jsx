import React from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable Notification Modal to replace native alert() and confirm()
 */
const NotificationModal = ({ 
  isOpen, 
  onClose, 
  type = 'info', 
  title, 
  message, 
  onConfirm 
}) => {
  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case 'success':
        return (
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <i className="bi bi-check-lg text-5xl text-green-600"></i>
          </div>
        );
      case 'error':
        return (
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <i className="bi bi-x-lg text-4xl text-red-600"></i>
          </div>
        );
      case 'warning':
        return (
          <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <i className="bi bi-exclamation-triangle-fill text-4xl text-yellow-600"></i>
          </div>
        );
      case 'confirm':
        return (
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <i className="bi bi-question-lg text-4xl text-blue-600"></i>
          </div>
        );
      default:
        return (
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <i className="bi bi-info-lg text-4xl text-gray-600"></i>
          </div>
        );
    }
  };

  const getButtonClass = () => {
    switch (type) {
      case 'success': return 'bg-green-600 hover:bg-green-700 shadow-green-200';
      case 'error': return 'bg-red-600 hover:bg-red-700 shadow-red-200';
      case 'warning': return 'bg-yellow-600 hover:bg-yellow-700 shadow-yellow-200';
      case 'confirm': return 'bg-blue-600 hover:bg-blue-700 shadow-blue-200';
      default: return 'bg-gray-800 hover:bg-gray-900 shadow-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center px-4 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-md transition-opacity duration-300"
        onClick={type !== 'confirm' ? onClose : undefined}
      ></div>
      
      {/* Modal Content */}
      <div className="relative bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl transform transition-all duration-300 scale-100 opacity-100 flex flex-col items-center text-center animate-in fade-in zoom-in slide-in-from-bottom-4 duration-300">
        
        {getIcon()}
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2 leading-tight">
          {title || (type === 'success' ? '¡Éxito!' : type === 'error' ? 'Error' : 'Atención')}
        </h2>
        
        <p className="text-gray-600 mb-8 text-lg font-medium leading-relaxed">
          {message}
        </p>
        
        <div className="flex gap-3 w-full">
          {type === 'confirm' ? (
            <>
              <button 
                onClick={onClose}
                className="flex-1 px-6 py-3.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-2xl transition-all active:scale-95"
              >
                Cancelar
              </button>
              <button 
                onClick={() => {
                  if (onConfirm) onConfirm();
                  onClose();
                }}
                className={`flex-1 px-6 py-3.5 text-white font-bold rounded-2xl shadow-lg transition-all active:scale-95 ${getButtonClass()}`}
              >
                Confirmar
              </button>
            </>
          ) : (
            <button 
              onClick={onClose}
              className={`w-full px-6 py-3.5 text-white font-bold rounded-2xl shadow-lg transition-all active:scale-95 ${getButtonClass()}`}
            >
              Entendido
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

NotificationModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  type: PropTypes.oneOf(['info', 'success', 'error', 'warning', 'confirm']),
  title: PropTypes.string,
  message: PropTypes.string.isRequired,
  onConfirm: PropTypes.func
};

export default NotificationModal;
