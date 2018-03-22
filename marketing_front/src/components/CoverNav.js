import React, { Component } from 'react';
import '../App.css'
import URI, { IMG_DEV_URL} from '../constants/serverUrl';

class CoverNav extends Component {

  render() {
    return (
      <div style={{ width: '100%',  zIndex: '99', position: 'absolute', width: '674px'}} className="row cover-nav">
        <div className="col-md-12" style={{ backgroundColor: 'rgba(0, 123, 255, 0.85)'}}>
          <div className="row">
            <div className="col-md-12">
              <div style={{padding: '38px 15px 29px 15px'}}>
                <span style={{color: '#fff'}} className="nav-link roman">Markets</span>
              </div>
            </div>
          </div>
          <div className="row">
            { this.props.markets.map(m => <div className="col-md-3" style={{paddingBottom: '29px'}}>
              <img src={URI+m.image} style={{width: '138px', height: '99px'}} />
              <span style={{color: '#fff', fontSize: '14px'}} className="nav-link roman">{m.name}</span>
              <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
            </div>) }
            { this.props.markets.map(m => <div className="col-md-3" style={{paddingBottom: '29px'}}>
              <img src={URI+m.image} style={{width: '138px', height: '99px'}} />
              <span style={{color: '#fff', fontSize: '14px'}} className="nav-link roman">{m.name}</span>
              <div style={{backgroundColor: 'rgba(255,255,255,0.4)', height: '2px', 'width': '100%'}}></div>
            </div>) }
          </div>
        </div>
      </div>
    );
  }
}

export default CoverNav
