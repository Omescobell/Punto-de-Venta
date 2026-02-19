import PropTypes from 'prop-types';

const ActionButtons = ({ onEdit, onDelete, children }) => {
  return (
    <td className="Action-Buttons">
      {onEdit && (
        <button className="button_edit" onClick={onEdit}>
          <i className="bi bi-pencil-square"></i>
        </button>
      )}
      {onDelete && (
        <button className="button_delete" onClick={onDelete}>
          <i className="bi bi-trash"></i>
        </button>
      )}
      {children}
    </td>
  );
};

ActionButtons.propTypes = {
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  children: PropTypes.node
};

export default ActionButtons;
