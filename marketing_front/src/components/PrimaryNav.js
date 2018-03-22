import React, { Component } from 'react';
import '../App.css'
import CoverNav from './CoverNav';
import { withRouter } from 'react-router'


class PrimaryNav extends Component {

  state = {
    show: false,
  }

  toggleShow = () => {
    this.setState({ show: !this.state.show})
  }

  changePage = (uri) => {
    this.setState({ show:false})
    this.props.changePage(uri)
  }

  render() {
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
              <a className="nav-link bold" onClick={() => this.changePage("/our_products/all")}>Products</a>
              <a className="nav-link bold" onClick={this.toggleShow}>Markets</a>
              <a className="nav-link bold" onClick={() => this.changePage("/support")}>Support</a>
              <a className="nav-link grey-text-dark roman" onClick={() => this.changePage("/news")}>News</a>
              <a className="nav-link  grey-text-dark roman" onClick={() => this.changePage("/about")}>About</a>
              {/*<a className="nav-link disabled roman" href="#">Contact</a>*/}
            </nav>
          </div>
          <div className="col-md-4"></div>
        </div>
        { this.state.show && <CoverNav markets={this.props.markets} changePage={this.props.changePage} onMouseOut={this.toggleShow}/> }
      </div>
    );
  }
}

export default withRouter(PrimaryNav)
