import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';

const SubHeader = ({ items, activeItem }) => {
  return (
    <div className="sub-header">
      {items.map((item) => (
        <label 
          key={item.path} 
          className={`sub-title ${activeItem === item.name ? 'active-sub' : ''}`}
        >
          <Link className="Small-List" to={item.path}>
            {item.name}
          </Link>
        </label>
      ))}
    </div>
  );
};

SubHeader.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      path: PropTypes.string.isRequired
    })
  ).isRequired,
  activeItem: PropTypes.string
};

export default SubHeader;
