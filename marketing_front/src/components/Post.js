import React, { Component } from 'react';
import { withRouter } from 'react-router'
import URI from '../constants/serverUrl';
//const URI = 'http://localhost:8000';

class Post extends Component {

  render() {
    const { post } = this.props;
    if(!post) {
      return <div />
    }
    return (
      <div className="row" style={{padding: '20px 40px 70px 20px'}}>
        <div className="col-md-12">
          <div className="row">
            <div className="col-md-12">
              <h1 className="header">{post.title}</h1>
            </div>
          </div>
          <div class = "row">
            <div className="col-md-12" style={{paddingTop: '45px'}}>
              { post.image && <img src={URI+post.image} className="wide" /> }
            </div>
          </div>
          <div className="row" style={{ marginTop: '40px', paddingBottom: '80px' }}>
            <div className="col-md-12">
              <p style={{whiteSpace: 'pre-wrap'}}>{post.content}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

}

export default withRouter(Post);
