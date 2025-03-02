import React, { Component } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { withRouter } from 'react-router';
import AutoComplete from 'react-autocomplete';
import './Navigation.css';

class MainNav extends Component {
  state = {
    searchVal: '',
    choices: [],
  }

  render() {
    return (
      <div className="primary-nav">
        <div className="top-bar">
          <div className="nav-link-wrap"><span>Call 0800 667 843</span></div>
          <div className="nav-link-wrap"><NavLink to="/about">About us</NavLink></div>
          <div className="nav-link-wrap"><NavLink to="/contact">Contact us</NavLink></div>
          <div className="nav-link-wrap">
            <NavLink to="/app">Login
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-person-circle nav-icon" viewBox="0 0 18 18">
                <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
                <path fillRule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1"/>
              </svg>
            </NavLink>
          </div>
        </div>
      </div>
    );
  }

  renderSearchItem = (item, isHighlighted) => (
    <div className={`search-item ${isHighlighted ? 'highlighted' : ''}`}>
      {item}
    </div>
  )
}

export default withRouter(MainNav);