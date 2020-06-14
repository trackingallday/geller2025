import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
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

    let home_row1_link = null;
    if (home_row1_col2.linkText && home_row1_col2.linkURL) {
      home_row1_link = <NavLink to={home_row1_col2.linkURL}>{home_row1_col2.linkText}</NavLink>
    }

    let latest_news_link = null;
    if (latest_news.linkText && latest_news.linkURL) {
      latest_news_link = <NavLink to={latest_news.linkURL}>{latest_news.linkText}</NavLink>
    }

    return (
      <div>
        <div className="row">
          <div className="col-md-6 col-lg-6 col-xs-12">
            <div className="main-message">
              <pre>{ mainBanner && mainBanner.content}</pre>
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
              <h1 className="header black-text news-home">{home_row1_col2.title}</h1>
              <div className="news-home">
                <pre  className="roman grey-text">
                  {home_row1_col2.content}
                </pre>
                {home_row1_link}
              </div>
            </div>
            <div className="col-md-6">
              <div className="contain" style={{minHeight: '280px'}}>
                <img src={URI+home_row1_col2.image} className="wide" />
              </div>
            </div>
        </div>
        <div className="row blue-back pad-top pad-left pad-bottom">
            <div className="col-md-6">
              <div className="top-right">
                <div className="hexagon blue"></div>
              </div>
              <h1 className="news-home header white-text">
                { latest_news.title }
              </h1>
              <div className="news-home">
                <pre className="roman white-text">{latest_news.content}</pre>
                {latest_news_link}
              </div>
            </div>
            <div className="col-md-6">
                <div className="contain" style={{minHeight: '280px'}}>
                  <img src={URI+latest_news.image} className="wide" />
                </div>
            </div>
        </div>
      </div>
    );
  }

}
