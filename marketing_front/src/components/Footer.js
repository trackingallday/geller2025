import React, { Component } from 'react';
import '../App.css';

export default class Footer extends Component {
  render() {
    return (
      <div className="row blue-back-dark footer-row">
        <div className="col-md-5 pad-left footer first">
          <nav className="nav foot-nav">
            <a className="nav-link white-text foot-nav-border first" href="/our_products/all">Products</a>
            <a className="nav-link white-text foot-nav-border" href="/our_products/all">Markets</a>
            <a className="nav-link white-text" href="/support">Support</a>
          </nav>
          <nav className="nav foot-nav">
            <a className="nav-link white-text foot-nav-border first" href="/news">News</a>
            <a className="nav-link white-text foot-nav-border" href="/about">About</a>
            <a className="nav-link white-text" href="/contact">Contact</a>
          </nav>
          <div>
            <span className="grey-text-light">© 2018 {this.props.configs.company_name_footer} | All rights reserved.</span>
          </div>
        </div>
        <div className="col-md-7 second">
          <h2 className="header white-text">Contact us now for a free quote:</h2>
          <h1 className="header massive-blue">{this.props.configs.ph_number}</h1>
          <div>
            <span className="white-text">or email {this.props.configs.email_address}</span>
          </div>
          <a href="/">
            <img src={require('../assets/Geller_WHITE.svg')} className="footer-logo"/>
          </a>
        </div>
      </div>
    );
  }
}
