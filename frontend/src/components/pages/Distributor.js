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
        newForm={NewProductForm}
        editForm={EditProductForm}
        recordsTable={ProductsTable}
        getDataFunc={getProducts}
        recordType="Product"
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
      (t, i) => (<Card.Grid key={i} style={gridStyle}>{ t }</Card.Grid>));
  }

  renderHome = () => {
    const { email, first_name, last_name, profile } = this.props.user;
    const { address, businessName, cellPhoneNumber, phoneNumber } = profile;

    const details = [ businessName, `${first_name} ${last_name}`, email, phoneNumber, cellPhoneNumber, address];
    const headings = ['Business', 'Name', 'Email', 'Phone', 'Cell', 'Address'];

    const customerNames = this.state.customers.map(c => c.businessName);
    const customerSheetLinks = this.state.customers.map(c => c.id);

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
                { this.renderCardGrid(customerNames) }
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
        <Route exact={true} path="/" render={this.renderHome} key={3} />
      </div>
    )
  }

}

export default DistributorPage;
