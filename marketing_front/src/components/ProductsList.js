import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import serverUrl from '../constants/serverUrl';


export default class ProductList extends Component {

  renderProduct = (p, ind) => {
    return (
      <div key={ind} className="col-md-3" style={{padding: '10px 15px'}}>
        <div className="row">
          <NavLink to={"/product/" + p.id} style={{margin: '0 auto'}}>
            <div className="contain" style={{height: '220px'}}>
              <img className="brighten" src={serverUrl + p.primaryImageLink} />
            </div>
          </NavLink>
        </div>
        <div className="row" style={{paddingTop: '15px'}}>
          <div className="col-md-12">
            <NavLink className="product-desc" style={{textDecoration: 'none'}} to={"/product/" + p.id}>
              <p>
                <span className="product-name">
                  { p.name }
                </span>
              </p>
            </NavLink>
          </div>
        </div>
        <div className="row" style={{paddingTop: '5px'}}>
          <div className="col-md-12">
            <div className="block-with-text product-desc" style={{maxHeight: '60px', lineHeight:'12px'}}>
              { p.subheading ? p.subheading : p.description }
            </div>
          </div>
        </div>
      </div>
    )
  }

  render() {
    console.log("list ", this.props.products)
    return (
      <div className="row" style={{paddingLeft: '10px', paddingRight: '20px'}}>
        { this.props.products.map(this.renderProduct) }
      </div>
    );
  }

}
