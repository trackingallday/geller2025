import React from 'react';
import NewCustomerForm from '../forms/NewCustomerForm';
import EditCustomerForm from '../forms/EditCustomerForm';
import NewProductForm from '../forms/NewProductForm';
import EditProductForm from '../forms/EditProductForm';
import RecordAdmin from '../common/RecordAdmin';
import ProductsTable from '../datatables/ProductsTable';
import CustomersTable from '../datatables/CustomersTable';
import { getProducts, getCustomers } from '../../util/DjangoApi';
import { Route, NavLink } from 'react-router-dom';
import { Menu, Row, Col, Icon, Card, } from 'antd';
import BasePage from './BasePage';
import styles from '../../styles';
import CustomerSheet from '../common/CustomerSheet';


const gridStyle = {
  width: '100%',
  textAlign: 'center',
  margin: 0,
};


class DistributorPage extends BasePage {

  state = {
    customers: [],
  }

  renderMenu() {
    return (
      <Row type="flex" justify="start">
        <Col span="20">
          <Menu
            theme="dark"
            mode="horizontal"
            style={{ lineHeight: '64px', width: '100%' }}
            selectedKeys={[window.location.pathname]}
          >
          <Menu.Item key="/">
            <NavLink exact to="/" label="Home">Home</NavLink>
          </Menu.Item>
          <Menu.Item key="/customers">
            <NavLink exact to="/customers" label="Customers">Customers</NavLink>
          </Menu.Item>
          <Menu.Item key="/products">
            <NavLink exact to="/products" label="Products">Products</NavLink>
          </Menu.Item>
         </Menu>
        </Col>
        <Col span="4">
          <Row type="flex" justify="end">
            <Col>
              <a onClick={this.logout} style={{ color: '#fff' }}>
                <Icon type="user-delete" style={{ fontSize: 20}} />
                <span style={{ fontSize: 14}}>Logout</span>
              </a>
            </Col>
          </Row>
        </Col>
      </Row>
    );
  }

  getDataAndLoading = (callback, getFunc) => {
    this.startLoading();
    getFunc((data) => {
      callback(data);
      this.stopLoading();
    });
  }

  getProducts = (callback) => {
    this.getDataAndLoading(callback, getProducts);
  }

  getCustomers = (callback) => {
    this.getDataAndLoading(callback, getCustomers);
  }

  renderDistributorProducts = () => {
    return (
      <RecordAdmin
        newForm={NewProductForm}
        editForm={EditProductForm}
        recordsTable={ProductsTable}
        getDataFunc={this.getProducts}
        recordType="Product"
        startLoading={this.startLoading}
        stopLoading={this.stopLoading}
      />
    );
  }

  renderDistributorCustomers = () => {
    return (
      <RecordAdmin
        newForm={NewCustomerForm}
        editForm={EditCustomerForm}
        recordsTable={CustomersTable}
        getDataFunc={this.getCustomers}
        recordType="Customer"
        startLoading={this.startLoading}
        stopLoading={this.stopLoading}
      />
    )
  }

  componentDidMount() {
    this.setState({
      loading: true,
    })
    getCustomers((customers) => {
      this.stopLoading();
      this.setState({ customers });
    });
  }

  renderCardGrid(contents) {
    return contents.map(
      (t, i) => (<Row key={`${i}_key`}>{ t }</Row>));
  }

  renderCustomerGrid(contents) {
    return contents.map((c, i) => (<Row key={i}><a href={`/customer_sheet/${c.id}`} target="blank">{c.businessName}</a></Row>));
  }

  renderCustomerSheet = () => {
    return (
      <CustomerSheet user={this.props.user} />
    );
  }

  renderHome = () => {
    const { email, first_name, last_name, profile } = this.props.user;
    const { address, businessName, cellPhoneNumber, phoneNumber } = profile;

    const details = [ businessName, `${first_name} ${last_name}`, email, phoneNumber, cellPhoneNumber, address];
    const headings = ['Business', 'Name', 'Email', 'Phone', 'Cell', 'Address'];

    return (
      <Row>
        <Col span="12">
          <Card title={ `My details` } style={{padding: 0}}>
            <Row>
              <Col span={"6"}>
                { this.renderCardGrid(headings) }
              </Col>
              <Col span={"18"}>
                { this.renderCardGrid(details) }
              </Col>
            </Row>
          </Card>
        </Col>
        <Col span="12">
          <Card title="My Customers" style={{padding: 0}}>
            <Row>
              <Col span={"24"}>
                { this.renderCustomerGrid(this.state.customers) }
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    )
  }

  renderContent() {
    return (
      <div style={styles.container}>
        <Route exact={true} path="/customers" render={this.renderDistributorCustomers} key={1} />
        <Route exact={true} path="/products" render={this.renderDistributorProducts} key={2} />
        <Route path="/customer_sheet/:customer_id" render={this.renderCustomerSheet} key={4} />
        <Route exact={true} path="/" render={this.renderHome} key={3} />
      </div>
    )
  }

}

export default DistributorPage;
