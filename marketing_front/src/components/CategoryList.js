import React, { Component } from 'react';

export default class CategoryList extends Component {

  onCategoryClick = (c) => {
    if(this.props.market) {
      this.props.history.push('/our_markets/' + c.id)
    } else {
      this.props.history.push('/our_products/' + c.id)
    }
  }

  renderCategory = (c, ind) => {
    if(c.id == this.props.category) {
      return (
        <li className="list-group-item smaller roman-med" key={ind} onClick={() => this.onCategoryClick(c)}>
          <span style={{color: '#0275d8'}}>
            {c.name}
          </span>
        </li>
      );
    }
    return (
      <li className="list-group-item smaller roman-med" key={ind} onClick={() => this.onCategoryClick(c)}>
        <span className="grey-text">{c.name}</span>
      </li>
    );
  }

  render() {
    return (
      <ul className="list-group list-group-flush">
        <li className="list-group-item smaller" style={{paddingBottom: '19px'}} key={'a'} onClick={() => this.onCategoryClick({id:null})}>
          <span className="roman grey-text-light roman-small">Products</span>
        </li>
        { this.props.categories.map(this.renderCategory) }
      </ul>
    );
  }

}
