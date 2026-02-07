import PropTypes from 'prop-types';

const ActionButtons = ({ onEdit, onDelete }) => {
  return (
    <td className="Action-Buttons">
      <button className="button_edit" onClick={onEdit}>
        <i className="bi bi-pencil-square"></i>
      </button>
      <button className="button_delete" onClick={onDelete}>
        <i className="bi bi-trash"></i>
      </button>
    </td>
  );
};

ActionButtons.propTypes = {
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export default ActionButtons;
