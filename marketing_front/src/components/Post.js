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
    let postLinkDOM = null;
    if (post.linkURL && post.linkText) {
      postLinkDOM = <div className="row">
                    <div className="col-md-12">
                      <p style={{whiteSpace: 'pre-wrap'}}>
                        <a href={post.linkURL}>{post.linkText}</a>
                      </p>
                    </div>
                  </div>
    }
    return (
      <div className="row" style={{padding: '20px 40px 70px 20px'}}>
        <div className="col-md-12">
          <div className="row">
            <div className="col-md-12">
              <h1 className="header">{post.title}</h1>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12" style={{paddingTop: '45px'}}>
              { post.image && <div className="contain" style={{width: '100%', minHeight: '300px'}}>
                  <img src={URI+post.image} />
                </div> }
            </div>
          </div>
          <div className="row" style={{ marginTop: '40px', paddingBottom: '80px' }}>
            <div className="col-md-12">
              <p style={{whiteSpace: 'pre-wrap'}}><pre>{post.content}</pre></p>
            </div>
          </div>
          { postLinkDOM }
        </div>
      </div>
    )
  }

}

export default withRouter(Post);
