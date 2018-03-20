import React, { Component } from 'react';
import '../../App.css'
import URI, { IMG_DEV_URL} from '../../constants/serverUrl';

//const URI = 'http://localhost:8000';



export default class Home extends Component {

  render() {
    const { posts } = this.props;
    const mainBanner = posts.find(p => p.name === 'main_banner_white');
    const home_row1_col2 = posts.find(p => p.name === 'home_row1_col2');
    const latest_news = posts.find(p => p.name === 'latest_news');

    if(!mainBanner) {
      return <div/>
    }
    return (
      <div>
        <div className="row">
          <div className="col-12">
            <div className="main-message">
              <p>
                { mainBanner && mainBanner.content}
              </p>
            </div>
          </div>
        </div>
        <div className="row pad-top back-white pad-bottom">
          <div className="col-6 pad-left">
            <h1 className="header black-text">{home_row1_col2.title}</h1>
            <p className="roman grey-text">
              {home_row1_col2.content}
            </p>
          </div>
          <div className="col-6" style={{padding: 0}}>
            <img src={URI+home_row1_col2.image} className="wide" />
          </div>
        </div>
        <div className="row blue-back">
          <div className="col-6 pad-top pad-left pad-bottom">
            <h1 className="header white-text">
              { latest_news.title }
            </h1>
            <p className="roman white-text">
              { latest_news.content }
            </p>
          </div>
          <div className="col-6 bobn-back cover">
            <img src={URI+latest_news.image} className="wide" />
          </div>
        </div>
      </div>
    );
  }

}
