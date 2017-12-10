import React, { Component } from 'react';
import NewCustomerForm from './components/common/NewCustomerForm';
import EditCustomerForm from './components/common/EditCustomerForm';
import ProductForm from './components/common/ProductForm';
import RecordAdmin from './components/common/RecordAdmin';
import ProductsTable from './components/distributor/ProductsTable';
import CustomersTable from './components/distributor/CustomersTable';
import { getProducts, getCustomers } from './util/DjangoApi';


import logo from './logo.svg';
import { Route, Link } from 'react-router-dom';
import { Layout, Menu, Icon, Row, Col } from 'antd';
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
      username: 'rimuboddy',
      password: 'cbr400rr'
    }).then((response) => {
      this.setState({
        token: `Token ${response.data.token}`,
      });
      localStorage.setItem('token', `Token ${response.data.token}`);
    }).catch((error) => {
      console.log(error);
    });
  }

  renderMenu() {
    return (
      <Row type="flex" justify="start">
        <Col span="20">
          <Menu
          theme="dark"
          mode="horizontal"
          style={{ lineHeight: '64px', width: '100%' }}
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
        </Col>
        <Col span="4">
          <Row type="flex" justify="end">
            <Col>
              <a href="/accounts/logout" style={{ color: '#fff' }}>
                <Icon type="user-delete" style={{ fontSize: 20}} />
                <span style={{ fontSize: 14}}>Logout</span>
              </a>
            </Col>
          </Row>
        </Col>
      </Row>
    );
  }

  renderDistributorProducts() {
    return (
      <RecordAdmin
        newForm={ProductForm}
        editForm={ProductForm}
        recordsTable={ProductsTable}
        getDataFunc={getProducts}
        recordType="Product"
        dataUrl="/products_list/"
      />
    );
  }

  renderDistributorCustomers() {
    return (
      <RecordAdmin
        newForm={NewCustomerForm}
        editForm={EditCustomerForm}
        recordsTable={CustomersTable}
        getDataFunc={getCustomers}
        recordType="Customer"
        dataUrl="/customers_list/"
      />
    )
  }

  render() {
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
            <Route exact path="/customers" render={this.renderDistributorCustomers} />
          <Route exact path="/products" render={this.renderDistributorProducts} />
          <Route exact path="/" render={() => <div>hi</div>} />
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
