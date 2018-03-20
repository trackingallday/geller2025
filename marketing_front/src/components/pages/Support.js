import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import CategoryList from '../CategoryList';
import PostList from '../PostList';
import { withRouter } from 'react-router'
import Post from '../Post';

import URI, { IMG_DEV_URL} from '../../constants/serverUrl';
//const URI = 'http://localhost:8000';
class Support extends Component {

  render() {
    return (
      <div>
        <div className="row" style={{ height: '80px'}}>
          <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '45px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div className="col-2" style={{ width: '191px'}}>
            <PostList posts={this.props.posts} post={this.props.post} />
          </div>
          <div className="col-9">
            <Post post={this.props.posts.find(p => p.id == this.props.post) || this.props.posts[0]} />
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(Support);
