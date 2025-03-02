import React, { Component } from 'react';
import { withRouter } from 'react-router';
import Hero from '../Hero/Hero';
import Hero3 from '../Hero3/Hero3';
import Hero2 from '../Hero2/Hero2';
import ArticleCol from '../AritcleCol/ArticleCol.js';
import ArticleRow from '../ArticleRow/ArticleRow.js';
//const URI = 'http://localhost:8000';

const blurb = `
We are the hygiene solution specialists, dedicated to creating a world
wherepeople can enjoy their environments with peace of mind 
knowing they are safe, clean and healthy.
`;

class About extends Component {
  
  render() {
    const { posts, products } = this.props;
    console.log(posts);
    console.log(products);
    const aboutus = posts.find(p => p.name === 'aboutus');
    const aboutus1 = posts.find(p => p.name === 'aboutus1');
    const postbottom1 = posts.find(p => p.name === 'homebottom1');
    const postbottom2 = posts.find(p => p.name === 'homebottom2');
    if(!aboutus) {
      return <div/>
    }
    return (
      <div>
        <Hero 
          subtitle="About Us"
          titleClass={'smaller-title'}
          title={aboutus.content}
          subtitleClass={'smaller-subtitle'}
          imgClass={'hero-image-about'}
        />
        <div className="container py-4">
          <div className="row g-4 py-4">
              <div className="col col-12 pt-2">
                <h1 className='hero-subtitle'>Our Products</h1>
              </div>
              <div class="col-12 pt-4 d-flex justify-content-center">
                <img src="/some-products.png" style={{width: '95%'}} />
              </div>
          </div>
          <div className="row g-4 py-4"></div>
          <div className="row g-4 py-4"></div>
        </div>
        <Hero3
          title="Sustainability"
          titleClass={'smaller-title'}
          subtitle={blurb}
          subtitleClass={'smaller-subtitle'}
          imgClass={'hero-image-about-2'}
        />
        <div className="container py-4">
          <div className="row g-4">
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <img src={'http://localhost:8000' + aboutus1.image} 
                  alt={aboutus1.title} className="middleimg"
                  style={{width: '100%', height: 'auto'}}
                />
              </div>
              <div className="col col-md-6 col-lg-6 col-xs-12 pt-2">
                <ArticleCol title={aboutus1.title} body={aboutus1.content} />
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

export default withRouter(About);
