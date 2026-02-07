import PropTypes from 'prop-types';

const SearchBar = ({ placeholder = "Buscar", value, onChange }) => {
  return (
    <div className="Search_Container">
      <input 
        type="text" 
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
      <i className="bi bi-search search-icon"></i>
    </div>
  );
};

SearchBar.propTypes = {
  placeholder: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func
};

export default SearchBar;
