import React, { Component } from 'react';
import '../App.css'
import URI, { IMG_DEV_URL} from '../constants/serverUrl';

class CoverNav extends Component {

  render() {
    return (
      <div onMouseLeave={this.props.onMouseOut} style={{ width: '100%',  zIndex: '99', position: 'absolute', width: '674px', paddingBottom: '15px'}} className="row cover-nav">
        <div className="col-md-12" style={{ backgroundColor: 'rgba(0, 123, 255, 0.9)'}}>
          <div className="row">
            <div className="col-md-12">
              <div style={{padding: '0px 0px 0px 0px'}}>
                <span style={{color: '#fff'}} className="nav-link roman">Markets</span>
              </div>
            </div>
          </div>
          <div className="row" style={{paddingBottom: '18px'}}>
            { this.props.markets.map(m =>
              <div className="col-md-3" style={{paddingBottom: '39px'}}>
                 <a className="cover" onClick={() => this.props.changePage("/our_products/all/" + m.id)}>
                   <img className="darken" src={'http://localhost:8000'+m.image} />
                 </a>
                 <a href="#" onClick={() => this.props.changePage("/our_products/all/" + m.id)}>
                   <span style={{color: '#fff', fontSize: '14px', textDecoration: 'none'}} className="nav-link roman">{m.name}</span>
                 </a>
                <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
              </div>) }
          </div>
        </div>
      </div>
    );
  }
}

export default CoverNav
