import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './HomeNav.css';
import searchIcon from '../../assets/search.svg';
import SectorsNav from './SectorsNav';

const HomeNav = () => {
  const [showSolutions, setShowSolutions] = useState(true);
  const [showSystems, setShowSystems] = useState(false);


  function handleSolutionsClick() {
    setShowSolutions(!showSolutions);
  }
  function handleSystemsClick() {
    setShowSystems(true);
  }
  const extraNav = showSolutions ? (
    <div className="hero-nav-extra">
      <SectorsNav />
    </div>
  ) : null;
  return <React.Fragment>
    { extraNav }
    <nav className="home-nav">
      <div className="home-nav-container">
        <div className="home-nav-links">
          <img src={searchIcon} alt="Search" className="products-search-icon" />
          <Link to="/our_products/1" className="nav-link">Products</Link>
          <a className="nav-link mylink" onClick={handleSolutionsClick}>Sectors</a>
          <a className="nav-link mylink">Solutions</a>
          <Link to="/support" className="nav-link">Support</Link>
        </div>
        <div className="search-sds-button">
          <img src={searchIcon} alt="Search" className="search-icon" />
          <Link to="/get-sds" className="sds-link">Search SDS</Link>
        </div>
      </div>
    </nav>
  </React.Fragment>
    
};

export default HomeNav;