import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import '../../App.css';
import './Sectors.css';
import serverUrl from '../../constants/serverUrl';
import HeaderSmall from '../HeaderSmall/HeaderSmall';
import ArticleCol from '../AritcleCol/ArticleCol';
import ArticleRow from '../ArticleRow/ArticleRow';
import Solutions from '../SolutionsGrid/SolutionsGrid';

export default class Sectors extends Component {
  render() {
    const { sector } = this.props;
    
    if (!sector) {
      return <div style={{height: '1000px'}} />;
    }

    // Featured product section
    let featuredProduct = null;
    if (sector.product_feature) {
      featuredProduct = (
        <div className="featured-product-section">
          <div className="container py-4">
            <div className="row">
              <div className="col-12">
                <h2 className="featured-product-heading">{sector.product_feature_title || 'Featured Product'}</h2>
              </div>
            </div>
            <div className="row g-4">
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <ArticleCol 
                  title={sector.product_feature.name} 
                  body={sector.product_feature_desccription || sector.product_feature.description}
                />
              </div>
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <img 
                  src={serverUrl + (sector.product_feature_image || sector.product_feature.primaryImageLink)} 
                  alt={sector.product_feature.name} 
                  className="sector-image"
                  style={{width: '100%', height: 'auto'}}
                />
              </div>
            </div>
          </div>
        </div>
      );
    }

    // News posts section
    let newsPosts = null;
    if (sector.news_post_1 || sector.news_post_2) {
      newsPosts = (
        <div className="news-section">
          <div className="container py-4">
            <div className="row">
              <div className="col-12">
                <h2 className="news-heading">Related News</h2>
              </div>
            </div>
            <div className="row g-4">
              {sector.news_post_1 && (
                <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                  <ArticleRow 
                    title={sector.news_post_1.title} 
                    image={sector.news_post_1.image}
                    body={sector.news_post_1.content} 
                    isHTMLBody={true}
                    titleColor={'#FFFFFF'} 
                    bgColor={'#32c8d4'} 
                    pColor={'#FFFFFF'} 
                    linkColor={'#FFFFFF'}
                  />
                </div>
              )}
              {sector.news_post_2 && (
                <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                  <ArticleRow 
                    title={sector.news_post_2.title} 
                    image={sector.news_post_2.image} 
                    body={sector.news_post_2.content}
                    isHTMLBody={true}
                    titleColor={'#32c8d4'} 
                    bgColor={'#5a2684'} 
                    pColor={'#FFFFFF'} 
                    linkColor={'#32c8d4'}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div>
        <HeaderSmall title={sector.name} />
        
        {/* Main sector description section */}
        <div className="container py-5 p-0">
          <div className="row g-4 p-0">
            <div className="col col-md-6 col-lg-6 col-xs-12 pt-2 p-0">
              <div className="content">
                <h1 className="sector-heading">{sector.name}</h1>
                <div className="sector-description" dangerouslySetInnerHTML={{ __html: sector.description }} />
              </div>
            </div>
            <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
              {sector.image && (
                <img 
                  src={serverUrl + sector.image} 
                  alt={sector.name} 
                  className="sector-image"
                  style={{width: '100%', height: 'auto'}}
                />
              )}
            </div>
          </div>
        </div>

        <Solutions items={sector.sections} />
        
        {/* Featured product */}
        {featuredProduct}
        
        {/* News posts */}
        {newsPosts}
      </div>
    );
  }
}