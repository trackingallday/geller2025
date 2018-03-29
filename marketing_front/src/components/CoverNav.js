import React, { Component } from 'react';
import '../App.css'
import URI, { IMG_DEV_URL} from '../constants/serverUrl';

class CoverNav extends Component {

  renderMarkets = () => {
    return this.props.markets.map(m =>
      <div className="col-md-3" style={{paddingBottom: '39px'}} key={m.id}>
         <a className="cover" onClick={() => this.props.changePage("/our_markets/" + m.id)}>
           <img className="darken" src={URI+m.image} />
         </a>
         <a href="#" onClick={() => this.props.changePage("/our_markets/all/" + m.id)}>
           <span style={{color: '#fff', fontSize: '13px', textDecoration: 'none'}} className="nav-link roman">{m.name}</span>
         </a>
        <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
      </div>)
  }

  renderCategories = () => {
    return this.props.categories.map(m =>
      <div className="col-md-3" style={{paddingBottom: '39px'}} key={m.id}>
         <a href="#" onClick={() => this.props.changePage("/our_products/" + m.id)}>
           <span style={{color: '#fff', fontSize: '13px', textDecoration: 'none'}} className="nav-link roman">{m.name}</span>
         </a>
        <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
      </div>);
  }

  render() {
    const label = this.props.markets ? 'Markets' : 'Categories';
    return (
      <div onMouseLeave={this.props.onMouseOut} style={{ width: '100%',  zIndex: '99', position: 'absolute', minHeight: '400px', backgroundColor: 'rgba(0, 123, 255, 0.9)' }} className="row cover-nav">
        <div className="col-md-12">
          <div className="row">
            <div className="col-md-12 ">
              <div style={{padding: '0px 0px 0px 0px'}}>
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
