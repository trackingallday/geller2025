import React, { Component } from 'react';
import ProductsList from '../ProductsList';
import PostList from '../PostList';
import { withRouter } from 'react-router'
import Post from '../Post';
import URI from '../../constants/serverUrl';
import ArticleCol from '../AritcleCol/ArticleCol';
import SmallCard from '../SmallCard/SmallCard';
import HeaderSmall from '../HeaderSmall/HeaderSmall';

class News extends Component {

  render() {
    const { posts } = this.props;
    const extraposts = [...posts, ...posts, ...posts];
    /* get the date "2022-09-06T00:38:09.707021Z" formatted like 25January */
    const formatDate = (date) => {
      const d = new Date(date);
      return d.getDate() + " " + d.toLocaleString('default', { month: 'long' });
    }

    const cards = extraposts.map(p => ({
      title: p.title,
      image: URI + p.image,
      body: formatDate(p.created_at),
    }));
      
    return (
      <div>
        <HeaderSmall title="News" />
        <div className="container py-4">
          <div className="row g-4 pt-4 pl-4 pb-0">
            <div className="col">
              <h1 className='myheadingnews' style={{color: "#5F259F"}}>
                Latest News
              </h1>
            </div>
          </div>
          <div className="row p-4 pt-0">
            {cards.map((card, index) => (
              <div className="col-md-6 col-sm-12 col-md-6 col-xl-3 col-lg-4 col-xs-12 pb-4" key={index}>
                <SmallCard title={card.title} image={card.image} body={card.body} />
              </div>
              ))}
          </div>
        </div>
      </div>
      
    );
  }

}

export default withRouter(News);
