import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'


class Product extends Component {

  onCategoryClick(c) {
    this.props.router.push('/our_products/' + c.id)
  }

  renderProductDetail(text, className="product-detail", heading=null) {
    return (
      <div className="col-md-12" style={{marginTop: heading ? '25px' : '5px'}}>
        { heading &&
             <div style={{fontSize: '12px', fontWeight: 'bold'}}>
              <span className="product-name">{heading}</span>
            </div>
        }
        <span className={className}>
          { text }
        </span>
      </div>
    )
  }

  render() {
    const p = this.props.product;
    console.log(this.props)
    return (
      <div>
        <div className="row" style={{ height: '80px'}}>
          <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div style={{ width: '191px'}}>
            <CategoryList
              categories={this.props.categories}
              onCategoryClick={this.onCategoryClick}
              category={p.productCategory}
              history={this.props.history}
            />
          </div>
          <div className="col-md-8" style={{padding: '10px 5px 10px 5px'}}>
            <div className="row">
              <div className="col-md-6">
                { this.renderProductDetail(p.name + " - " + p.brand, "product-name")}
                { this.renderProductDetail("SKU: " + p.productCode, "product-detail tiny-text")}
                { this.renderProductDetail(p.marketingDesc)}
                { this.renderProductDetail(p.description, "product-detail", "description")}
                { this.renderProductDetail(p.usageType, "product-detail", "usage")}
                { this.renderProductDetail(p.market) }
              </div>
              <div className="col-md-6 cover" style={{height: '400px' }}>
                <a href={"/product/" + p.id}><img src={p.primaryImageLink} /></a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Product);
