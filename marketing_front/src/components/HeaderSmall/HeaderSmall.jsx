import React from "react";
import './HeaderSmall.css';

const HeaderSmall = () => {
  return (
    <nav className="navbar navbar-expand-lg d-flex justify-content-end myheader"
      style={{ backgroundColor: "#5F259F"}}>
        {/* Brand Name */}
        <img class="small-header-logo" src="/static/media/new_geller_white.afc828d5.svg"></img>

        {/* Navbar Items */}
        <div className="d-flex ms-auto justify-content-end w-100">
          <a className="nav-link text-white small" href="#">Products</a>
          <a className="nav-link text-white small" href="#">Solutions</a>
          <a className="nav-link text-white small" href="#">Systems</a>
          <a className="nav-link text-white small" href="#">Support</a>

          {/* Button */}
          <button className="btn btn-info text-white-50 small rounded-pill">
            <span className="small">Search for SDS</span>
          </button>
        </div>
    </nav>
  );
};

export default HeaderSmall;
