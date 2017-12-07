import React, { Component } from 'react';
import DistributorCustomers from './components/distributor/DistributorCustomers';
import logo from './logo.svg';
import { Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import axios from 'axios';
import serverUrl from './constants/serverUrl';
import './App.css';



const { Header, Footer, Content } = Layout;


const distProducts = () => (
  <div>Hello Products</div>
);


class App extends Component {

  state = {
    token: null,
  }

  componentDidMount() {
    axios.post(serverUrl + '/get_auth_token/', {
      username: 'dist1',
      password: 'cbr400rr'
    }).then((response) => {
      console.log(response.data);
      this.setState({
        token: `Token ${response.data.token}`,
      });
    }).catch((error) => {
      console.log(error);
    });
  }

  renderMenu() {
    return (
      <Menu
        theme="dark"
        mode="horizontal"
        defaultSelectedKeys={['customers']}
        style={{ lineHeight: '64px' }}
      >
        <Menu.Item key="home">
          <Link to="/" label="Home">Home</Link>
        </Menu.Item>
        <Menu.Item key="customers">
          <Link to="/customers" label="Customers">Customers</Link>
        </Menu.Item>
        <Menu.Item key="products">
          <Link to="/products" label="Products">Products</Link>
        </Menu.Item>
      </Menu>
    );
  }

  renderDistributorCustomer = () => {
      return (<DistributorCustomers token={this.state.token} />)
  }

  render() {
    const token = this.state.token;
    if(!this.state.token) {
      return (<div>helloo woeld</div>)
    }
    return (
      <Layout className="layout">
        <Header>
          <div className="logo" />
          { this.renderMenu() }
        </Header>
        <Content>
          <div style={{ background: '#fff', padding: 12, minHeight: 600 }}>
            <Route path="/customers" render={this.renderDistributorCustomer} />
          <Route path="/products" render={this.renderDistributorCustomer} />
            <Route path="/" component={distProducts} token={token} />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          Cleaning Chemical Data Sheets & Safety Info
        </Footer>
      </Layout>
    );
  }
}

export default App;
