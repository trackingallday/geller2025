import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import URI from '../../constants/serverUrl';


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
    return (
      <div>
        <div className="row" style={{ height: '80px'}}>
          <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '170px'}}>
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
                { this.renderProductDetail(p.description)}
                { this.renderProductDetail(p.application, "product-detail", "Applications")}
                { this.renderProductDetail(p.properties, "product-detail", "Properties")}
                { this.renderProductDetail(p.market) }
              </div>
              <div className="col-md-6" style={{height: '400px' }}>
                <div className="row">
                  <div className="col-md-12">
                    <a href={"/product/" + p.id}><img src={p.primaryImageLink} /></a>
                  </div>
                  <div className="col-md-12">
                    <a href={URI+p.infoSheet} target="_blank" className={"nav-link roman"}>
                      <div className="roman grey-text">
                        <img src={require('../../assets/pdf-icoin.png')} style={{width: '26px'}}/>
                        <span style={{position: 'absolute', top: '20px', left: '50px', fontSize: '12px'}}>Download Info Sheet</span>
                      </div>
                    </a>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Product);
