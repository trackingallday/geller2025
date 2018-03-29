import React, { Component } from 'react';
import '../App.css'
import CoverNav from './CoverNav';
import { withRouter } from 'react-router';
import { NavLink, Link } from 'react-router-dom';


class PrimaryNav extends Component {

  state = {
    show: false,
  }

  toggleShow = () => {
    this.setState({ show: !this.state.show})
  }

  changePage = (uri) => {
    this.setState({ show:false})
    this.props.changePage(uri);
  }

  render() {
    const path = window.location.pathname;
    const isMarketsActive = path.indexOf('markets') !== -1
    return (
      <div style={{paddingRight: '140px'}}>
        <div className="row top-nav-row" style={{height: '100px', backgroundColor: '#fff', }}>
          <div className="col-md-8 back-white top-nav-col">
            <nav className="nav top-nav">
              <a className="nav-link" href="https://app.integraindustries.co.nz/app" target="_blank">
                <img src={require('../assets/login.svg')} className="icon" />
                <span>Login</span>
              </a>
              <a className="nav-link home" href="/">
                <img src={require('../assets/house-outline.svg')} className="icon" />
                <span>Home</span>
              </a>
            </nav>
          </div>
          <div className="col-md-3"></div>
        </div>
        <div className="row bottom-nav-row" style={{backgroundColor: '#fff'}}>
          <div className="col-md-8 back-white">
            <nav className="nav top-nav">
              <NavLink className="nav-link bold" activeClassName="active" to="/our_products/all">Products</NavLink>
              <NavLink className="nav-link bold" activeClassName="active" isActive={() => isMarketsActive} to={path} onClick={this.toggleShow}>Markets</NavLink>
              <NavLink className="nav-link bold" to="/support" activeClassName="active">Support</NavLink>
              <NavLink className="nav-link grey-text roman" activeClassName="active" to="/news">News</NavLink>
              <NavLink className="nav-link  grey-text roman" activeClassName="active" to="/about">About</NavLink>
              <a className="nav-link grey-text roman" href="#">Contact</a>
            </nav>
          </div>
          <div className="col-md-4"></div>
        </div>
        { this.state.show && <CoverNav markets={this.props.markets} changePage={this.changePage} onMouseOut={this.toggleShow}/> }
      </div>
    );
  }
}

export default withRouter(PrimaryNav)
