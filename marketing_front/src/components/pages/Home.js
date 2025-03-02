import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import '../../App.css'
import serverUrl, { IMG_DEV_URL} from '../../constants/serverUrl';
import Hero from '../Hero/Hero';
import Hero2 from '../Hero2/Hero2';
import ArticleCard from '../AritcleCard/ArticalCard';
import ArticleCol from '../AritcleCol/ArticleCol';
import ArticleRow from '../ArticleRow/ArticleRow';

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
      let style = {};
      if (home_row1_col2.linkColor && home_row1_col2.linkColor !== '#000000') {
        style.color = home_row1_col2.linkColor;
      }
      home_row1_link = <NavLink style={style} to={home_row1_col2.linkURL}>{home_row1_col2.linkText}</NavLink>
    }

    let latest_news_link = null;
    if (latest_news.linkText && latest_news.linkURL) {
      let style = {};
      if (latest_news.linkColor && latest_news.linkColor !== '#000000') {
        style.color = latest_news.linkColor;
      }
      latest_news_link = <NavLink style={style} to={latest_news.linkURL}>{latest_news.linkText}</NavLink>
    }
    const postHome1 = posts.find(p => p.name === 'home_1');
    const postHome2 = posts.find(p => p.name === 'home2');
    const postHome3 = posts.find(p => p.name === 'home3');
    const postHome4 = posts.find(p => p.name === 'home4');
    const cards = [
      { title: "Ultimo System", image: serverUrl + postHome1.image, body: postHome1.content },
      { title: "Online Training", image: serverUrl + postHome2.image, body: postHome2.content },
      { title: "Sustainability", image: serverUrl + postHome3.image, body: postHome3.content },
      { title: "NZ Made", image: serverUrl + postHome4.image, body: postHome4.content }
    ];
    const cards2 = [
      { title: "Ultimo System", image: serverUrl + postHome1.image, body: postHome1.content },
      { title: "Online Training", image: serverUrl + postHome2.image, body: postHome2.content },
    ];
    const cards3 = [
      { title: "Sustainability", image: serverUrl + postHome3.image, body: postHome3.content },
    ];
    const postmiddle = posts.find(p => p.name === 'homemiddle');
    const postbottom1 = posts.find(p => p.name === 'homebottom1');
    const postbottom2 = posts.find(p => p.name === 'homebottom2');
    const title = "Dedicated to supporting you every day, in every way, with every care in the world.";
    const subtitle = "We are";
    const btnText = "Search our range";
    return (
      <div>
        <Hero title={title} subtitle={subtitle} btnText={btnText} />
        <div className="container py-4">
          <div className="row g-4">
            {cards.map((card, index) => (
              <div className="col col-md-6 col-lg-3 col-xs-12 pt-2" key={index}>
                <ArticleCard title={card.title} image={card.image} body={card.body} />
              </div>
            ))}
          </div>
        </div>
        <Hero2 />
        
        <div className="container py-4">
          <div className="row g-4">
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <img src={serverUrl + postmiddle.image} 
                  alt={postmiddle.title} className="middleimg"
                  style={{width: '100%', height: 'auto'}}
                />
              </div>
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <ArticleCol title={postmiddle.title} body={postmiddle.content} />
              </div>
          </div>
        </div>
        <div className="bg-gray-100">
          <div className="container py-4">
            <div className="row g-4">
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <ArticleRow title={postbottom1.title} image={postbottom1.image}
                  body={postbottom1.content} titleColor={'#FFFFFF'} bgColor={'#7ED4E3'} pColor={'#000000'} linkColor={'#FFFFFF'}
                />
              </div>
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <ArticleRow title={postbottom2.title} image={postbottom2.image} body={postbottom2.content}
                  titleColor={'#7ED4E3'} bgColor={'#4B2E83'} pColor={'#FFFFFF'} linkColor={'#7ED4E3'}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}
