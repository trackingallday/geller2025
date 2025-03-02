import React, { Component } from 'react';
import MainNav from './components/Navigation/MainNav';
import Hero from './components/Hero/Hero';
import Footer from './components/Footer/Footer';
import Home from './components/pages/Home';
import Products from './components/pages/Products';
import Product from './components/pages/Product';
import About from './components/pages/About';
import Support from './components/pages/Support';
import News from './components/pages/News';
import Contact from './components/pages/Contact';
import NotFound from './components/pages/NotFound';
import GetSDS from './components/pages/GetSDS';
import URI from  './constants/serverUrl';

import MobileNav from './components/MobileNav';
import { Route, NavLink, Switch } from 'react-router-dom';
import { withRouter } from 'react-router';
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
        console.log(data);
        this.setState({data, loaded: true});
      });
  }

  withConfigs(Component) {
    return (matchProps) => {
      return <Component configs={ this.state.data.configs } {...matchProps} />
    }
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
      sizes: [],
    }
  }

  componentDidMount() {
  }

  search = (value) => {
    const { products, markets, categories } = this.state.data;
    const product = products.find(p => p.name === value)
    if(product) {
      return this.changePage('/product/' + product.id);
    }
    const category = categories.find(p => p.name === value)
    if(category) {
      return this.changePage('/our_products/' + category.id);
    }
    const market = markets.find(p => p.name === value)
    if(market) {
      return this.changePage('/our_markets/' + market.id);
    }
  }

  autoCompleteChoices() {
    const { products, categories, markets } = this.state.data;
    return [...products.map(p=>p.name), ...categories.map(p => p.name), ...markets.map(m => m.name)];
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
    return product ? <Product product={product} categories={this.state.data.categories} sizes={this.state.data.sizes} /> : this.renderProducts(match);
  }

  renderAbout = (match) => {
    return <About posts={this.state.data.posts} products={this.state.data.products} />
  }

  renderSupport = (match) => {
    return <Support posts={this.state.data.posts.filter(p => p.page === 'Support')} post={match.match.params.post} />
  }

  renderNews = (match) => {
    return <News posts={this.state.data.posts.filter(p => p.page === 'News')} post={match.match.params.post} />
  }

  renderContact = (match) => {
    const product = this.state.data.products.find(p => p.id == match.match.params.product_id);
    let contactMessage = product && product.name || '';
    let productId = product && product.id || undefined;
    return <Contact configs={ this.state.data.configs } message={ contactMessage } product={productId} />
  }

  renderSDS = (match) => {
    const productId = match.match.params.product_id;
    const product = this.state.data.products.find(p => p.id == productId);
    const productName = product && product.name || undefined;
    return <GetSDS configs={ this.state.data.configs } productName={ productName } productId={ productId } />
  }

  render() {
    const isHome = window.location.pathname === '/';

    return (
      <React.Fragment>
        <MainNav 
          markets={this.state.data.markets} 
          changePage={this.changePage} 
          categories={this.state.data.categories} 
          search={this.search} 
          choices={this.autoCompleteChoices()} 
        />
        <Switch>
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
          <Route exact={true} path="/contact/:product_id" render={(m) => this.renderContact(m)} key={19} />
          <Route exact={true} path="/getsds/:product_id" render={(m) => this.renderSDS(m)} key={501} />
          <Route component={this.withConfigs(NotFound)} />
        </Switch>
        <div className="container">
          <Footer configs={this.state.data.configs} />
        </div>
        
        {!this.state.loaded && (
          <div className="loading-overlay" />
        )}
      </React.Fragment>
    );
  }
}

export default withRouter(App);
