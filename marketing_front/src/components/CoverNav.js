import React, { Component } from 'react';
import '../App.css'
import URI, { IMG_DEV_URL} from '../constants/serverUrl';
import { NavLink } from 'react-router-dom';


class CoverNav extends Component {

  renderMarkets = () => {
    return this.props.markets.map(m =>
      <div className="col-md-3" style={{paddingBottom: '39px'}} key={m.id}>
        <NavLink to={"/our_markets/" + m.id}>
         <div className="cover" style={{height: '80px', width: '100%'}}>
           <img className="darken" src={URI+m.image} />
         </div>
       </NavLink>
         <NavLink to={"/our_markets/" + m.id}  style={{textDecoration: 'none'}}>
           <span style={{color: '#fff', fontSize: '13px'}} className="nav-link roman darken">{m.name}</span>
         </NavLink>
        <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
      </div>)
  }

  renderCategories = () => {
    return this.props.categories.map(m =>
      <div className="col-md-3" style={{paddingBottom: '10px'}} key={m.id}>
        <div style={{minHeight: '45px'}}>
          <NavLink to={"/our_products/" + m.id} style={{textDecoration: 'none'}}>
            <span style={{color: '#fff', fontSize: '11px'}} className="nav-link roman darken">{m.name}</span>
          </NavLink>
        </div>
        <div style={{backgroundColor: 'rgba(255,255,255,0.5)', height: '3px', 'width': '100%', bottom: '0px'}}></div>
      </div>);
  }

  render() {
    const label = this.props.markets ? 'Markets' : 'Categories';
    return (
      <div onClick={() => {debugger;this.props.onMouseOut()}} style={{ width: '100%',  zIndex: '99', position: 'absolute', minHeight: '400px', backgroundColor: 'rgba(0, 123, 255, 0.9)' }} className="row cover-nav">
        <div className="col-md-12"  onMouseLeave={this.props.onMouseOut}>
          <div className="row">
            <div className="col-md-12 ">
              <div style={{padding: '0px 0px 20px 0px'}}>
                <span style={{color: '#fff'}} className="nav-link roman">{label}</span>
              </div>
            </div>
          </div>
          <div className="row" style={{paddingBottom: '2px'}}>
            <div className="col-md-7">
              <div className="row">
                { !!this.props.markets && this.renderMarkets()  }
                { !!this.props.categories && this.renderCategories()  }
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default CoverNav
