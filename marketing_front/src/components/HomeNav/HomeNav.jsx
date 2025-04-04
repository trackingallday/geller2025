import React from 'react';
import { Link } from 'react-router-dom';
import './HomeNav.css';
import searchIcon from '../../assets/search.svg';

const HomeNav = () => {
  return (
    <nav className="home-nav">
      <div className="home-nav-container">
        <div className="home-nav-links">
          <Link to="/products" className="nav-link">Products</Link>
          <Link to="/solutions" className="nav-link">Solutions</Link>
          <Link to="/systems" className="nav-link">Systems</Link>
          <Link to="/support" className="nav-link">Support</Link>
        </div>
        <div className="search-sds-button">
          <img src={searchIcon} alt="Search" className="search-icon" />
          <Link to="/get-sds" className="sds-link">Search SDS</Link>
        </div>
      </div>
    </nav>
  );
};

export default HomeNav;