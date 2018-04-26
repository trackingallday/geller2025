import React, { Component } from 'react';

export default class CategoryList extends Component {

  onCategoryClick = (c) => {
    if(this.props.market) {
      this.props.history.push('/our_markets/' + c.id);
    } else {
      this.props.history.push('/our_products/' + c.id);
    }
  }

  onSubCategoryClick = (c) => {
    this.props.history.push('/our_products/' + this.props.category + '/' + c.replace(/\s+/g, ''));
  }

  renderSubCategory = (sc) => {
    const style = sc && sc.replace(/\s+/g, '') === this.props.subCategory ? {color: '#0275d8'} : {};

    return (
      <li key={sc} className="list-group-item roman-med brighten" onClick={() => this.onSubCategoryClick(sc)}>
        <span className={"blue-text-light "} style={style} >{ sc }</span>
      </li>
    );
  }

  renderCategory = (c, ind) => {
    if(c.id == this.props.category) {
      return (
        <li className="list-group-item smaller roman-med brighten" key={ind}>
          <div>
            <div>
              <span style={{color: '#0275d8'}} onClick={() => this.onCategoryClick(c)}>
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
        <span className="grey-text darken">{c.name}</span>
      </li>
    );
  }

  render() {
    return (
      <ul className="list-group list-group-flush">
        <li className="list-group-item smaller" style={{paddingBottom: '19px'}} key={'a'} onClick={() => this.onCategoryClick({id:'all'})}>
          <span className="roman grey-text-light darken roman-small" style={{fontSize: '14px'}}>All Products</span>
        </li>
        { this.props.categories.map(this.renderCategory) }
      </ul>
    );
  }

}
