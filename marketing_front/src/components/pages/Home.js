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
          <div className="col-md-6 col-lg-6 col-xs-12">
            <div className="main-message">
              <p>
                { mainBanner && mainBanner.content}
              </p>
            </div>
          </div>
          <div className="col-md-7">
          </div>
        </div>
        <div className="row pad-top back-white pad-bottom">
            <div className="col-md-6 pad-left">
              <div className="top-right">
                <div className="hexagon white"></div>
              </div>
              <h1 className="header black-text">{home_row1_col2.title}</h1>
              <p className="roman grey-text">
                {home_row1_col2.content}
              </p>
            </div>
            <div className="col-md-6" style={{padding: 0}}>
              <img src={URI+home_row1_col2.image} className="wide" />
            </div>
        </div>
        <div className="row blue-back pad-top pad-left pad-bottom">
            <div className="col-md-6">
              <div className="top-right">
                <div className="hexagon blue"></div>
              </div>
              <h1 className="header white-text">
                { latest_news.title }
              </h1>
              <p className="roman white-text">
                { latest_news.content }
              </p>
            </div>
            <div className="col-md-6 bobn-back cover">
              <img src={URI+latest_news.image} className="wide" />
            </div>
        </div>
      </div>
    );
  }

}
