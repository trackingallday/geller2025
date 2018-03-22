import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import URI, { IMG_DEV_URL} from '../../constants/serverUrl';
//const URI = 'http://localhost:8000';

class Products extends Component {

  state = {
    category: null,
    market: null,
  }

  onCategoryClick = (c) => {
    this.setState({category: c });
  }

  componentDidMount() {
  }

  render() {
    if(this.props.products.length === 0) {
      return <div style={{height: '1000px'}} />
    }
    let category = this.state.category || this.props.categories.find(c => c.id == this.props.category);
    let market = null;
    let products = this.props.products;
    if(category) {
      products = this.props.products.filter(p => p.productCategory == category.id);
    } else if (this.props.market) {
      market = this.props.markets.find(c => c.id == this.props.market);
      products = this.props.products.filter(p => !!p.markets.find(m => m == this.props.market));
    }

    const categoryName = category ? category.name : 'All Products';
    const categoryDesc = category ? category.description : '';
    const marketName = market ? " - " + market.name : '';
    return (
      <div>
        <div className="row" style={{ height: '80px'}}>
          <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div className="col-md-2" style={{ width: '191px'}}>
            <CategoryList category={this.state.category || this.props.category} categories={this.props.categories} onCategoryClick={this.onCategoryClick} history={this.props.history} />
          </div>
          <div className="col-md-1"></div>
          <div className="col-md-9">
            <div className="row" style={{height: '150px', paddingTop: '35px'}}>
              <div className="col-md-1">
                <img src={require('../../assets/category-logo.png')} style={{width: '45px', height: '45px'}} />
              </div>
              <div className="col-md-6">
                <span  style={{paddingLeft: '9px'}} className="heading">{ categoryName }</span>
                <span  style={{paddingLeft: '0px'}} className="heading">{ marketName }</span>
              </div>
              <div className="col-md-6">
                <span className="description-text grey-text" style={{display: 'inline-block', lineHeight: '14px', paddingLeft: '9px', wordWrap: ''}}>
                  { categoryDesc }
                </span>
              </div>
                <div className="col-md-12">
                  <span className="roman-smaller grey-text-light" style={{fontSize: '11px', textAlign: 'left'}}>
                    { products.length + ' products'}
                  </span>
                </div>
            </div>
            <ProductsList category={this.state.category || this.props.category} products={products} market={this.props.market} />
            <div className="row" style={{paddingRight: '20px'}}>
              <div className="col-md-12" style={{ textAlign: 'right'}}>
                <div style={{backgroundColor: '#0275d8', height: '1px', width: '100%', marginTop: '30px'}} />
                <div style={{marginTop: '9px'}}>
                  <span className="roman-smaller grey-text-light">
                    { products.length + ' products'}
                  </span>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Products);
