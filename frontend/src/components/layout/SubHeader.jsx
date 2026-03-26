import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';

const SubHeader = ({ items, activeItem }) => {
  return (
    <div className="flex flex-row justify-center items-center gap-4 sm:gap-10 px-4 sm:px-[15%] mb-8 w-full flex-wrap">
      {items.map((item) => {
        const isActive = activeItem === item.name;
        return (
          <label key={item.path} className="m-0 cursor-pointer">
            <Link 
              className={`block text-lg sm:text-[24px] transition-colors rounded-lg
                ${isActive ? 'bg-[#E0E0E0] text-gray-900 font-semibold px-5 py-2.5 shadow-sm' : 'text-gray-600 hover:bg-gray-100 px-4 py-2 font-medium'}`}
              to={item.path}
            >
              {item.name}
            </Link>
          </label>
        );
      })}
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
