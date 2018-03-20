import React, { Component } from 'react';
import { withRouter } from 'react-router'


class PostList extends Component {

  onPostClick = (c) => {
    this.props.history.push('/' + window.location.pathname.split('/')[1] + '/' + c.id)
  }

  renderPost = (c, ind) => {
    if(c.id == this.props.post) {
      return (
        <li className="list-group-item smaller roman-med" key={ind} onClick={() => this.onPostClick(c)}>
          <span style={{color: '#0275d8'}}>
            {c.name}
          </span>
        </li>
      );
    }
    return (
      <li className="list-group-item smaller roman-med" key={ind} onClick={() => this.onPostClick(c)}>
        <span className="grey-text">{c.name}</span>
      </li>
    );
  }

  render() {
    return (
      <ul className="list-group list-group-flush">
        <li className="list-group-item smaller" style={{paddingBottom: '19px'}} key={'a'} onClick={() => this.onPostClick({id:null})}>
          <span className="roman grey-text-light roman-small">{this.props.title}</span>
        </li>
        { this.props.posts.map(this.renderPost) }
      </ul>
    );
  }

}

export default withRouter(PostList)
