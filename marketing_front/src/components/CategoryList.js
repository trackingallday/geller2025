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
    const style = sc.name && sc.id == this.props.subCategory ? 
      {color: '#4B2E83', textDecoration: 'underline', fontSize: '11px', fontWeight: 100} : 
      {color: 'white', fontSize: '11px', fontWeight: 100};
    return (
      <li key={sc.name+"subCategory"} 
          style={{backgroundColor: 'inherit', border: 'none', padding: '0.25rem 1.5rem', width: '100%'}} 
          className="list-group-item roman-med brighten category-item" 
          onClick={() => this.onSubCategoryClick(sc)}>
        <span className={"blue-text-light category-text"} style={style}>{ sc.name }</span>
      </li>
    );
  }

  renderCategory = (c, ind) => {
    if(c.id == this.props.category) {
      return (
        <li className="list-group-item smaller roman-med brighten category-item" 
            key={ind} 
            style={{
              marginLeft: '-1em', 
              border: 'none',
              padding: '0.25rem 1.5rem',
              width: '100%'
            }}>
          <div>
            <div style={{marginLeft: '1em' }}>
              <span style={{color: '#4B2E83', fontSize: '11px'} }
                    className="category-text"
                    onClick={() => this.onCategoryClick(c)}>
                <b>{'>'} {c.name}</b>
              </span>
            </div>
            <div>
              <ul className="list-group list-group-flush" style={{border: 'none', width: '100%'}}>
                { this.props.subCategories && this.props.subCategories.map(this.renderSubCategory) }
              </ul>
            </div>
          </div>
        </li>
      );
    }
    return (
      <li className="list-group-item smaller roman-med category-item" 
          key={ind} 
          onClick={() => this.onCategoryClick(c)} 
          style={{
            border: 'none', 
            padding: '0.25rem 1.5rem',
            width: '100%'
          }}>
        <span className="category-text" style={{color: '#8C8C8C', fontSize: '11px', fontWeight: 100}}>{c.name}</span>
      </li>
    );
  }

  render() {
    return (
      <ul className="list-group list-group-flush" style={{border: 'none', width: '100%'}}>
        <li className="list-group-item smaller category-item" 
            style={{padding: '0.25rem 1.5rem', border: 'none', width: '100%'}} 
            key={'a'} 
            onClick={() => this.onCategoryClick({id:'all'})}>
          <span className="category-text" style={{color: '#8C8C8C', fontSize: '11px', fontWeight: 100}}>All Products</span>
        </li>
        { this.props.categories.filter(c => !c.isSubCategory).map(this.renderCategory) }
      </ul>
    );
  }

}
