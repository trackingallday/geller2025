import React, { Component } from 'react';

export default class ProductList extends Component {

  renderProduct = (p, ind) => {
    return (
      <div key={ind} className="col-3" style={{padding: '10px 5px 10px 5px'}}>
        <div className="row">
          <div className="col-12 cover" style={{height: '200px' }}>
            <a href={"/product/" + p.id}><img src={p.primaryImageLink} /></a>
          </div>
        </div>
        <div className="row" style={{paddingTop: '15px'}}>
          <div className="col-12">
            <a className="product-desc" style={{textDecoration: 'none'}} href={"/product/" + p.id}>
              <span className="product-name">
                { p.name }
              </span>
            </a>
          </div>
        </div>
        <div className="row" style={{paddingTop: '5px'}}>
          <div className="col-12">
            <div className="block-with-text">
              <span className="product-desc" style={{display:'inline-block', lineHeight:'12px', maxHeight: '30px'}}>
                { p.description }
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  render() {
    const products = this.props.showingProducts || this.props.products;
    return (
      <div className="row">
        { products.map(this.renderProduct) }
      </div>
    );
  }

}
