import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import { NavLink } from 'react-router-dom';
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
            <div className="col-md-6">
              <div className="med-right">
                <div className="hexagon white"></div>
              </div>
              <div style={{height: '80px', width: '100%'}}></div>
          </div>
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
              <div className="col-md-6" style={{height: '350px' }}>
                <div className="row">
                  <div className="col-md-2" />
                  <div className="col-md-10" align="center">
                    <div className="contain" style={{margin: 'auto'}}>
                      <img src={p.primaryImageLink}></img>
                    </div>
                  </div>
                </div>
                <div className="row"  style={{padding: '0px 0px 0px 0px'}}>
                  <div className="col-md-3" />
                  <div className="col-md-9" style={{padding: '0px 60px 0px 0px'}}>
                    <a href={URI+p.infoSheet} target="_blank" className={"nav-link roman"}>
                      <div className="roman grey-text" style={{paddingLeft: '15px'}}>
                        <img src={require('../../assets/pdf-icoin.png')} style={{width: '26px'}} />
                        <span style={{position: 'absolute', top: '20px', left: '65px', fontSize: '12px'}}>Download Info Sheet</span>
                      </div>
                    </a>
                    <a href={'/contact/' + p.name } className={"nav-link roman"}>
                      <div className="roman grey-text" style={{paddingLeft: '15px'}}>
                        <img src={require('../../assets/pdf-icoin.png')} style={{width: '26px'}} />
                        <span style={{position: 'absolute', top: '60px', left: '65px', fontSize: '12px'}}>Enquire for SDS Sheet</span>
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
