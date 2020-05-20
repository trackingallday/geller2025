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

  renderProductDetail(text, className="product-detail", heading=null, size=null) {
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

    const aSizes = this.props.sizes.filter(a => !!a.isBag);
    const bSizes = this.props.sizes.filter(a => !a.isBag);

    const sizes = [];

    if(bSizes.filter(siz => !!p.sizes.find(ps => ps === siz.id)).length){
      bSizes.forEach(aS => {
        if(p.sizes.find(ps => ps === aS.id)) {
          sizes.push(<img key={"a"+aS.id} src={URI + aS.image} style={{height: '52px',  width:'33px', padding: '3px'}}></img>);
        } else {
          sizes.push(<img key={"a"+aS.id} src={URI + aS.imageNo} style={{height: '52px', width:'33px', padding: '3px'}}></img>);
        }
      });
    }

    if(aSizes.filter(siz => !!p.sizes.find(ps => ps === siz.id)).length){
      aSizes.forEach(aS => {
        if(p.sizes.find(ps => ps === aS.id)) {
          sizes.push(<img key={"b"+aS.id}  src={URI + aS.image} style={{height: '52px',  width:'33px', padding: '3px'}}></img>);
        } else {
          sizes.push(<img key={"b"+aS.id}  src={URI + aS.imageNo} style={{height: '52px', width:'33px', padding: '3px'}}></img>);
        }
      });
    }

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
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '270px'}}>
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
                { this.renderProductDetail(p.name + " - " + p.brand, "product-name-detail", null, "20px")}
                { this.renderProductDetail("SKU: " + p.productCode, "product-detail tiny-text")}
                { this.renderProductDetail(p.description)}
                { this.renderProductDetail(p.application, "product-detail", "Applications")}
                { this.renderProductDetail(p.properties, "product-detail", "Properties")}
                { this.renderProductDetail(p.market) }
              </div>
              <div className="col-md-6" style={{height: '350px' }}>
                <div className="row">
                  <div className="col-md-10" align="center">
                    <div className="contain" style={{margin: 'auto'}}>
                      <img className="main-product-img" src={URI + p.primaryImageLink}></img>
                    </div>
                  </div>
                </div>
                <div className="row" style={{height: '50px'}}>
                  <div className="col-md-12" style={{paddingTop: '12px'}}>
                    <span className="nav-link bold" style={{fontSize: '15px'}}>Available Sizes</span>
                  </div>
                </div>
                <div className="row" style={{minHeight: '100px'}}>
                  <div className="col-md-8 col-xs-12 col-sm-12">
                    { sizes }
                  </div>
                  <div className="col-md-4 col-xs-12 col-sm-12 pdf-links">
                    <div className="row justify-content-center">
                      <div className="col-lg-6  col-md-auto" style={{padding: '0px 0px 0px 0px'}}>
                        <a href={URI+p.infoSheet} target="_blank" className={"nav-link roman"}>
                          <div className="roman grey-text">
                            <img src={require('../../assets/pdf-icoin.png')} style={{width: '24px'}} />
                            <span style={{position: 'absolute', top: '15px', left: '32px', fontSize: '12px'}}>Info</span>
                            <span style={{position: 'absolute', top: '28px', left: '32px', fontSize: '8px'}}>(download)</span>
                          </div>
                        </a>
                      </div>
                      <div className="col-lg-6 col-md-auto" style={{padding: '0px 0px 0px 0px'}}>
                        <a href={'/contact/' + p.name } className={"nav-link roman"}>
                          <div className="roman grey-text" style={{paddingLeft: '20px'}}>
                            <img src={require('../../assets/pdf-icoin.png')} style={{width: '24px'}} />
                            <span style={{position: 'absolute', top: '15px', left: '50px', fontSize: '12px'}}>SDS</span>
                            <span style={{position: 'absolute', top: '28px', left: '50px', fontSize: '8px'}}>(enquire)</span>
                          </div>
                        </a>
                      </div>
                    </div>
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
