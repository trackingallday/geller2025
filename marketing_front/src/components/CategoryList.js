import React, { Component } from 'react';

export default class CategoryList extends Component {

  categoryMenuColor = (c) => {
    let category_menu_color = '#00c7c5';
    if (c && c.menu_color && c.menu_color != '#000000' && c.menu_color != '#000') {
      category_menu_color = c.menu_color;
    }
    return category_menu_color;
  }

  onCategoryClick = (c) => {
    if(this.props.market) {
      this.props.history.push('/our_markets/' + c.id);
    } else {
      this.props.history.push('/our_products/' + c.id);
    }
  }

  onSubCategoryClick = (c) => {
    this.props.history.push('/our_products/' + this.props.category + '/' + c.id);
  }

  renderSubCategory = (sc) => {
    if(!sc.isSubCategory){
      return null;
    }
    const style = sc.name && sc.id == this.props.subCategory ? {color: 'white', textDecoration: 'underline'} : { color: 'white' };
    return (
      <li key={sc.name+"subCategory"} style={{backgroundColor: 'inherit'}} className="list-group-item roman-med brighten" onClick={() => this.onSubCategoryClick(sc)}>
        <span className={"blue-text-light "} style={style} >{ sc.name }</span>
      </li>
    );
  }

  renderCategory = (c, ind) => {
    if(c.id == this.props.category) {
      return (
        <li className="list-group-item smaller roman-med brighten" key={ind} style={{backgroundColor: this.categoryMenuColor(c), marginLeft: '-1em'}}>
          <div>
            <div style={{marginLeft: '1em' }}>
              <span style={{color: 'white'}} onClick={() => this.onCategoryClick(c)}>
                {c.name}
              </span>
            </div>
            <div>
              <ul className="list-group list-group-flush">
                { this.props.subCategories && this.props.subCategories.map(this.renderSubCategory) }
              </ul>
            </div>
          </div>
        </li>
      );
    }
    return (
      <li className="list-group-item smaller roman-med" key={ind} onClick={() => this.onCategoryClick(c)}>
        <span className="grey-text brighten-blue">{c.name}</span>
      </li>
    );
  }

  render() {
    return (
      <ul className="list-group list-group-flush">
        <li className="list-group-item smaller" style={{paddingBottom: '19px'}} key={'a'} onClick={() => this.onCategoryClick({id:'all'})}>
          <span className="roman grey-text-light darken roman-small" style={{fontSize: '16px'}}>All Products</span>
        </li>
        { this.props.categories.filter(c => !c.isSubCategory).map(this.renderCategory) }
      </ul>
    );
  }

}
