import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
export default class ProductList extends Component {

  renderProduct = (p, ind) => {
    return (
      <div key={ind} className="col-md-3" style={{padding: '10px 0px 10px 0px'}}>
        <div className="row" style={{padding: '0px 20px 0px 0px'}}>
          <NavLink to={"/product/" + p.id}>
            <div className="col-md-12 contain" style={{height: '220px'}}>
              <img className="brighten" src={p.primaryImageLink} />
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
            <div className="block-with-text" style={{maxHeight: '48px'}}>
                <pre><span className="product-desc" style={{display:'inline-block', lineHeight:'12px'}}>
                  { p.description }
                </span></pre>
            </div>
          </div>
        </div>
      </div>
    )
  }

  render() {
    const products = this.props.showingProducts || this.props.products;
    return (
      <div className="row" style={{paddingLeft: '10px', paddingRight: '20px'}}>
        { products.map(this.renderProduct) }
      </div>
    );
  }

}
