import React, { Component } from 'react';
import '../App.css'

export default class Footer extends Component {
  render() {
    return (
      <div className="row blue-back-dark footer-row">
        <div className="col-5 pad-left footer first">
          <nav className="nav foot-nav">
            <a className="nav-link white-text foot-nav-border first" href="#">Products</a>
            <a className="nav-link white-text foot-nav-border" href="#">Markets</a>
            <a className="nav-link white-text" href="#">Support</a>
          </nav>
          <nav className="nav foot-nav">
            <a className="nav-link white-text foot-nav-border first" href="#">News</a>
            <a className="nav-link white-text foot-nav-border" href="#">About</a>
            <a className="nav-link white-text" href="#">Contact</a>
          </nav>
          <div className="bottom">
            <span className="grey-text-light">© 2018 Integra Industries | All rights reserved.</span>
          </div>
        </div>
        <div className="col-7 second">
          <h2 className="header white-text">Contact us now for a free quote:</h2>
          <h1 className="header massive-blue">0800 090 090</h1>
          <div className="bottom">
            <span className="white-text">or email sales@geller.co.nz</span>
          </div>
          <img src={require('../assets/Geller_WHITE.svg')} className="footer-logo"/>
        </div>
      </div>
    );
  }
}
