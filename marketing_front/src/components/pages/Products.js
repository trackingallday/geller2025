import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import { withRouter } from 'react-router'
import URI, { IMG_DEV_URL} from '../../constants/serverUrl';
import HeaderSmall from '../HeaderSmall/HeaderSmall';
//const URI = 'http://localhost:8000';

class Products extends Component {

  state = {
    category: null,
    market: null,
  }

  categoryMenuColor = (c) => {
    let category_menu_color = '#00c7c5';
    if (c && c.menu_color && c.menu_color != '#000000' && c.menu_color != '#000') {
      category_menu_color = c.menu_color;
    }
    return category_menu_color;
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
    let products = [...this.props.products];
    let subCategories = [...categories.filter(c => c.isSubCategory)];

    if(category) {
      products = this.props.products.filter(p => p.productCategory.find(e => e == category.id));
      subCategories = subCategories.filter(sc => sc.relatedCategory.indexOf(category.id) !== -1);
      subCategories.forEach(sc => {
        const prods = this.props.products.filter(p => p.subCategory.find(e => e == sc.id));
        prods.forEach(p => {
          if(!products.find(pp => pp.id === p.id)){
            products.push(p);
          }
        })
      })
    } else if (this.props.market) {
      market = markets.find(c => c.id == this.props.market);
      products = market ? this.props.products.filter(p => !!p.markets.find(m => m == this.props.market)) : this.props.products;
    }


    if(subCategory_id) {
      const subCategory = categories.find(c => c.id == subCategory_id);
      products = this.props.products.filter(
        p => !!( p.productCategory.indexOf(parseInt(subCategory_id)) !== -1) || p.subCategory.indexOf(parseInt(subCategory_id)) !== -1);
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
        <HeaderSmall title={name} />
        <div className="container">
          <div className="row" style={{backgroundColor: '#FFF', paddingTop: '15px', paddingBottom: '70px'}}>
            <div className="col-md-3" style={{ width: '300px'}}>
              { !!categories.length && <CategoryList category={this.state.category || this.props.category} subCategories={subCategories} subCategory={subCategory_id} categories={categories} onCategoryClick={this.onCategoryClick} history={this.props.history} />}
              { !categories.length && <CategoryList category={this.state.market || this.props.market} subCategories={subCategories} categories={markets} onCategoryClick={this.onMarketClick} history={this.props.history} market />}
            </div>
            <div className="col-md-1"></div>
            <div className="col-md-8">
              <div className="row" style={{minHeight: '215px', paddingTop: '35px'}}>
                { img }
                <div className="col-8">
                  <span  style={{paddingLeft: '0px', fontSize: '24px', color: '#4B2E83' }} className="heading">{ name || 'All Products' }</span>
                </div>
                <div className="col-8">
                  <span className="description-text grey-text" style={{padding: '20px 0px 10px 0px', display: 'inline-block', lineHeight: '17px', paddingRight: '9px', fontSize: '11pt', fontWeight: 100}}>
                    { categoryDesc }
                  </span>
                </div>
                  <div className="col-md-12">
                    <span className="roman-smaller grey-text-light" style={{fontSize: '14px', textAlign: 'left'}}>
                      { products.length + ' products'}
                    </span>
                  </div>
              </div>

              <ProductsList category={this.state.category || this.props.category} subCategory={categories.find(c => c.id == subCategory_id)} products={products} market={this.props.market} />

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
      </div>
    );
  }

}

export default withRouter(Products);
