import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import URI, { IMG_DEV_URL} from '../../constants/serverUrl';
//const URI = 'http://localhost:8000';

class Products extends Component {

  state = {
    category: null,
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
    const category = this.state.category || this.props.categories.find(c => c.id == this.props.category);
    let products = this.props.products;
    if(category) {
      products = this.props.products.filter(p => p.productCategory == category.id);
    }
    const categoryName = category ? category.name : 'All Products';
    const categoryDesc = category ? category.description : '';
    return (
      <div>
        <div className="row" style={{ height: '80px'}}>
          <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div style={{ width: '191px'}}>
            <CategoryList category={this.state.category || this.props.category} categories={this.props.categories} onCategoryClick={this.onCategoryClick} history={this.props.history} />
          </div>
          <div className="col-md-1"></div>
          <div className="col-md-8">
            <div className="row" style={{height: '150px', paddingTop: '35px'}}>
              <div className="col-md-1">
                <img src={require('../../assets/category-logo.png')} style={{width: '45px', height: '45px'}} />
              </div>
              <div className="col-md-4">
                <span  style={{paddingLeft: '9px'}} className="heading">{ categoryName }</span>
              </div>
              <div className="col-md-7">
                <span className="description-text grey-text" style={{display: 'inline-block', lineHeight: '14px', paddingLeft: '9px', wordWrap: ''}}>
                  { categoryDesc }
                </span>
              </div>
              <div className="row">
                <div className="col-md-12">
                  <span className="roman-smaller grey-text-light" style={{fontSize: '11px', marginLeft: '15px'}}>
                    { products.length + ' products'}
                  </span>
                </div>
              </div>
            </div>
            <div className="row">
              <ProductsList category={this.state.category || this.props.category} products={products}  />
            </div>
            <div className="row">
              <div style={{backgroundColor: '#0275d8', height: '1px', width: '100%', marginTop: '30px'}} />
              <div className="col-md-12" style={{ textAlign: 'right', marginRight: '10px'}}>
                <span className="roman-smaller grey-text-light">
                  { products.length + ' products'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Products);
