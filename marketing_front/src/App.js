import React, { Component } from 'react';
import PrimaryNav from './components/PrimaryNav';
import Footer from './components/Footer';
import Home from './components/pages/Home';
import Products from './components/pages/Products';
import Product from './components/pages/Product';
import About from './components/pages/About';
import Support from './components/pages/Support';
import News from './components/pages/News';
import Contact from './components/pages/Contact';
import URI from  './constants/serverUrl';

import MobileNav from './components/MobileNav';
import { Route, NavLink } from 'react-router-dom';
import { withRouter } from 'react-router'
import reqeust from 'superagent';
import './App.css'


class App extends Component {

  constructor() {
    super()
    reqeust.get(URI + '/public_products/')
      .end((err, res) => {
        let data = JSON.parse(res.text);
        let c = {};
        data.configs.forEach(co => c[co.name] = co.val)
        data.configs = c;
        this.setState({data, loaded: true});
      });
  }

  changePage = (url) => {
    this.props.history.push(url);
  }

  state = {
    data: {
      posts: [],
      products: [],
      categories: [],
      markets: [],
      configs: {},
    }
  }

  componentDidMount() {
  }

  renderHome() {
    return <Home posts={this.state.data.posts} />
  }

  renderProducts = (match) => {
    return <Products
      products={this.state.data.products}
      categories={this.state.data.categories}
      category={match.match.params.category_id}
      market={match.match.params.market_id}
      markets={this.state.data.markets}
      subCategory_id={match.match.params.subCategory_id}
    />
  }

  renderMarkets = (match) => {
    return <Products
      products={this.state.data.products}
      categories={[]}
      category={'all'}
      market={match.match.params.market_id}
      markets={this.state.data.markets}
    />
  }

  renderProduct = (match) => {
    const product = this.state.data.products.find(p => p.id == match.match.params.product_id);
    return product ? <Product product={product} categories={this.state.data.categories} /> : this.renderProducts(match);
  }

  renderAbout = (match) => {
    return <About posts={this.state.data.posts.filter(p => p.page === 'About')} post={match.match.params.post}  />
  }

  renderSupport = (match) => {
    return <Support posts={this.state.data.posts.filter(p => p.page === 'Support')} post={match.match.params.post} />
  }

  renderNews = (match) => {
    return <News posts={this.state.data.posts.filter(p => p.page === 'News')} post={match.match.params.post} />
  }

  renderContact = (match) => {
    return <Contact configs={ this.state.data.configs } message={match.match.params.message}/>
  }

  render() {
    const isHome = window.location.pathname === '/';
    const outImg = (
      <div style={{height: '560px', width:'100%', position: 'absolute', overflow:'hidden'}}>
        <div className="pulse circle"></div>
      </div>
    );
    const inImg = (
      <div className="pulse circle"></div>
    );

    return (
      <div>
        { isHome && outImg }
        <div className="container" style={{overflow: 'hidden', paddingRight: '0px'}}>
          <img src={require('./assets/geller.svg')} className="hexagons" />
          { !isHome && inImg }
          <PrimaryNav markets={this.state.data.markets} changePage={this.changePage} categories={this.state.data.categories} />
          <MobileNav />
          <Route exact={true} path="/" render={(match) => this.renderHome()} key={1} />
          <Route exact={true} path="/our_products/:category_id" render={(m) => this.renderProducts(m)} key={2} />
          <Route exact={true} path="/our_products/:category_id/:subCategory_id" render={(m) => this.renderProducts(m)} key={59} />
          <Route exact={true} path="/product/:product_id" render={(m) => this.renderProduct(m)} key={3} />
          <Route exact={true} path="/product/:product_id/:market_id" render={(m) => this.renderProduct(m)} key={3006} />
          <Route exact={true} path="/our_markets/:market_id" render={(m) => this.renderMarkets(m)} key={300} />
          <Route exact={true} path="/our_markets" render={(m) => this.renderMarkets(m)} key={30009} />
          <Route exact={true} path="/about/:post" render={(m) => this.renderAbout(m)} key={4} />
          <Route exact={true} path="/about" render={(m) => this.renderAbout(m)} key={42} />
          <Route exact={true} path="/news" render={(m) => this.renderNews(m)} key={49} />
          <Route exact={true} path="/news/:post" render={(m) => this.renderNews(m)} key={9} />
          <Route exact={true} path="/support/:post" render={(m) => this.renderSupport(m)} key={10} />
          <Route exact={true} path="/support" render={(m) => this.renderSupport(m)} key={11} />
          <Route exact={true} path="/contact" render={(m) => this.renderContact(m)} key={12} />
          <Route exact={true} path="/contact/:message" render={(m) => this.renderContact(m)} key={19} />

          <div className="row pad-top blue-back-dark">
            <div className="col-md-6">
              <div className="top-right">
                <div className="hexagon blue-dark"></div>
              </div>
            </div>
          </div>
          <Footer configs={this.state.data.configs} />
        </div>
        { !this.state.loaded && <div style={{position: 'absolute', height: '100%', width: '100%', top: 0, bottom: 0, left: 0, right: 0, backgroundColor: '#fff', zIndex: 9999}} /> }
      </div>
    );
  }
}

export default withRouter(App);
