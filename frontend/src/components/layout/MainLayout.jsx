import { Outlet } from 'react-router-dom';
import '../../styles/General.css';

const MainLayout = () => {
  return (
    <div className="app-container">
      <Outlet />
    </div>
  );
};

export default MainLayout;
