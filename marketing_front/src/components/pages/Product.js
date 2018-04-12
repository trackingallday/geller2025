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
    const sizes = this.props.sizes.map(s => {
      if(p.sizes.find(ps => ps === s.id)) {
        return (<img src={"http://0.0.0.0:8000" + s.image} style={{height: '52px',  width:'33px', padding: '3px'}}></img>);
      } else {
        return  (<img src={"http://0.0.0.0:8000" + s.imageNo} style={{height: '52px', width:'33px', padding: '3px'}}></img>);
      }
    })
    console.log(sizes);
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
                { this.renderProductDetail(p.name + " - " + p.brand, "product-name")}
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
                      <img src={p.primaryImageLink}></img>
                    </div>
                  </div>
                </div>
                <div className="row" style={{height: '50px'}}>
                  <div className="col-md-12" style={{paddingTop: '12px'}}>
                    <span className="nav-link bold" style={{fontSize: '15px'}}>Available Sizes (Litres)</span>
                  </div>
                </div>
                <div className="row" style={{height: '50px'}}>
                  <div className="col-md-6">
                    { sizes }
                  </div>
                  <div className="col-md-3" style={{padding: '5px 0px 0px 0px'}}>
                    <a href={URI+p.infoSheet} target="_blank" className={"nav-link roman"}>
                      <div className="roman grey-text">
                        <img src={require('../../assets/pdf-icoin.png')} style={{width: '26px'}} />
                        <span style={{position: 'absolute', top: '15px', left: '36px', fontSize: '12px'}}>Info (download)</span>
                      </div>
                    </a>
                  </div>
                  <div className="col-md-3" style={{padding: '5px 0px 0px 0px'}}>
                    <a href={'/contact/' + p.name } className={"nav-link roman"}>
                      <div className="roman grey-text" style={{paddingLeft: '1px'}}>
                        <img src={require('../../assets/pdf-icoin.png')} style={{width: '26px'}} />
                        <span style={{position: 'absolute', top: '15px', left: '36px', fontSize: '12px'}}>SDS (enquire)</span>
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
