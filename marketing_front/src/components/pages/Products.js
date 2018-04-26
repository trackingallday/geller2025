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

  onMarketClick = (c) => {
    this.setState({market: c });
  }

  componentDidMount() {
  }

  render() {
    if(this.props.products.length === 0) {
      return <div style={{height: '1000px'}} />
    }
    const { markets, categories, subCategory_id } = this.props;
    let category = this.state.category || categories.find(c => c.id == this.props.category);
    let market = null;
    let products = this.props.products;
    let subCategories = [];
    if(category) {
      products = this.props.products.filter(p => p.productCategory.find(e => e == category.id));
      subCategories = [...new Set(products.map(p => p.subCategory))];
    } else if (this.props.market) {
      market = markets.find(c => c.id == this.props.market);
      products = market ? this.props.products.filter(p => !!p.markets.find(m => m == this.props.market)) : this.props.products;
    }

    if(subCategory_id) {
      products = products.filter(p => p.subCategory && p.subCategory.replace(/\s+/g, '') === subCategory_id);
    }

    const categoryDesc = category ? category.description : '';
    let name = market ? market.name : 'All Products';
    name = category ? category.name : name;
    let img = null;
    if(category && category.image) {
      img = <div className="col-md-1"><img src={URI + category.image} style={{width: '45px', height: '45px'}} /></div>
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
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '30px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div className="col-md-2" style={{ width: '191px'}}>
            { !!categories.length && <CategoryList category={this.state.category || this.props.category} subCategories={subCategories} subCategory={subCategory_id} categories={categories} onCategoryClick={this.onCategoryClick} history={this.props.history} />}
            { !categories.length && <CategoryList category={this.state.market || this.props.market} subCategories={subCategories} categories={markets} onCategoryClick={this.onMarketClick} history={this.props.history} market />}
          </div>
          <div className="col-md-1"></div>
          <div className="col-md-9">
            <div className="row" style={{height: '150px', paddingTop: '35px'}}>
              { img }
              <div className="col-md-3">
                <span  style={{paddingLeft: '0px', fontSize: '24px'}} className="heading">{ name || 'All Products' }</span>
              </div>
              <div className="col-md-8">
                <span className="description-text grey-text" style={{display: 'inline-block', lineHeight: '14px', paddingRight: '9px', wordWrap: ''}}>
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
