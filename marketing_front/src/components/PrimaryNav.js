import React, { Component } from 'react';
import '../App.css'
import CoverNav from './CoverNav';
import { withRouter } from 'react-router';
import { NavLink, Link } from 'react-router-dom';
import AutoComplete from 'react-autocomplete';


class PrimaryNav extends Component {

  state = {
    showMarkets: false,
    showCategories: false,
    searchVal: '',
    choices: [],
  }

  toggleShowMarkets = () => {
    if(this.state.showCategories) {
      this.setState({showCategories: false, showMarkets: true})
    } else {
      this.setState({ showMarkets: !this.state.showMarkets});
    }

  }

  toggleShowCategories = () => {
    if(this.state.showMarkets) {
      this.setState({showMarkets: false, showCategories: true})
    } else {
      this.setState({ showCategories: !this.state.showCategories});
    }
  }

  changePage = (uri) => {
    this.setState({ showMarkets:false, showCategories: false})
    this.props.changePage(uri);
  }

  render() {
    const path = window.location.pathname;
    const isMarketsActive = path.indexOf('markets') !== -1;
    const isProductsActive = path.indexOf('product') !== -1;
    let coverNav = null;
    if(this.state.showCategories) {
      coverNav = <CoverNav categories={this.props.categories} changePage={this.changePage} onMouseOut={this.toggleShowCategories}/>
    }
    if(this.state.showMarkets) {
      coverNav = <CoverNav markets={this.props.markets} changePage={this.changePage} onMouseOut={this.toggleShowMarkets} />
    }
    const menuStyle = {
      borderRadius: '3px',
      boxShadow: '0 2px 12px rgba(0, 0, 0, 0.1)',
      background: 'rgba(255, 255, 255, 0.9)',
      padding: '2px 0',
      fontSize: '90%',
      position: 'fixed',
      overflow: 'auto',
      maxHeight: '50%', // TODO: don't cheat, let it flow to the bottom
      zIndex: 6,
    }
    return (
      <div style={{paddingRight: '150px'}}>
        <div className="row top-nav-row" style={{height: '100px', backgroundColor: '#fff', }}>
          <div className="col-md-8 back-white top-nav-col">
            <nav className="nav top-nav" style={{marginLeft: '0px'}}>
              <a className="nav-link" href="/app" target="_blank">
                <img src={require('../assets/login.svg')} className="icon" />
                <span style={{marginLeft: '5px'}}>Login</span>
              </a>
              <a className="nav-link" style={{marginTop: '7px'}}>
                <img src={require('../assets/search.svg')} className="icon" />

                <div className="auto-input" style={{ width: 200, marginLeft: '10px', border: 'none', display: 'inline-block' }}>
                  <AutoComplete
                    items={this.state.choices}
                    onChange={(e, v) => {
                      this.setState({searchVal: v});
                      if(v) {
                        let opts = this.props.choices.filter(c => c.toUpperCase().indexOf(v.toUpperCase()) !== -1);
                        this.setState({ choices: opts });
                      } else {
                        this.setState({ choices: this.props.choices});
                      }
                    }}
                    renderItem={(item, isHighlighted) =>
                      <div key={item+isHighlighted} style={{backgroundColor: isHighlighted ? '#e3e4e5':'#fff', position: 'relative', zIndex: 99, padding:"0px 0px 0px 8px"}}>
                        <span className="roman">{item}</span>
                      </div>
                    }
                    menuStyle={menuStyle}
                    value={this.state.searchVal}
                    getItemValue={(ee) => ee}
                    onSelect={(val) => {
                      this.setState({ searchVal: val });
                      this.props.search(val);
                    }}
                  />
                </div>

              </a>
            </nav>
          </div>
          <div className="col-md-3"></div>
        </div>
        <div className="row bottom-nav-row" style={{backgroundColor: '#fff'}}>
          <div className="col-md-8 back-white">
            <nav className="nav top-nav">
              <NavLink className="nav-link bold" activeClassName="active" isActive={() => isProductsActive} to={path} onClick={this.toggleShowCategories}>Products</NavLink>
              <NavLink className="nav-link bold" activeClassName="active" isActive={() => isMarketsActive} to={path} onClick={this.toggleShowMarkets}>Markets</NavLink>
              <NavLink className="nav-link bold" to="/support" activeClassName="active">Support</NavLink>
              <NavLink className="nav-link grey-text roman" activeClassName="active" to="/news">News</NavLink>
              <NavLink className="nav-link  grey-text roman" activeClassName="active" to="/about">About</NavLink>
              <NavLink className="nav-link grey-text roman"  activeClassName="active" to="/contact">Contact</NavLink>
            </nav>
          </div>
          <div className="col-md-4"></div>
        </div>
        { coverNav }
      </div>
    );
  }
}

export default withRouter(PrimaryNav)
