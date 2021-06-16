import React from 'react';
import NewCustomerForm from '../forms/NewCustomerForm';
import EditCustomerForm from '../forms/EditCustomerForm';
import NewProductForm from '../forms/NewProductForm';
import EditProductForm from '../forms/EditProductForm';
import RecordAdmin from '../common/RecordAdmin';
import ProductsTable from '../datatables/ProductsTable';
import CustomersTable from '../datatables/CustomersTable';
import { getProducts, getCustomers, getSafetyWears, getCategories, getSizes, getMarkets } from '../../util/DjangoApi';
import { Route, NavLink } from 'react-router-dom';
import { Menu, Row, Col, Icon, Card, Button } from 'antd';
import BasePage from './BasePage';
import styles from '../../styles';
import CustomerSheet from '../common/CustomerSheet';


class DistributorPage extends BasePage {

  state = {
    customers: [],
    products: [],
    safetyWears: [],
    distributors: [],
    markets: [],
    categories: [],
    sizes: [],
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
          <Menu.Item key="/app">
            <NavLink exact to="/app" label="Home">Home</NavLink>
          </Menu.Item>
          <Menu.Item key="/customers">
            <NavLink exact to="/customers" label="Customers">Customers</NavLink>
          </Menu.Item>
          <Menu.Item key="/products">
            <NavLink exact to="/products" label="Products">Products</NavLink>
          </Menu.Item>
          { this.renderDownloadLink() }

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

  getRecordsData = (dataFunction, name) => {
    return new Promise(resolve => {
      dataFunction((records) => {
        this.setState({
          [name]: records,
        });
        resolve(records);
      });
    });
  }

  renderDistributorProducts = () => {
    return (
      <RecordAdmin
        newForm={NewProductForm}
        editForm={EditProductForm}
        recordsTable={ProductsTable}
        getDataFunc={() => this.loadData(getProducts, 'products')}
        customers={this.state.customers}
        markets={this.state.markets}
        categories={this.state.categories}
        sizes={this.state.sizes}
        records={this.state.products}
        safetyWears={this.state.safetyWears}
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
        records={this.state.customers}
        products={this.state.products}
        getDataFunc={() => this.loadData(getCustomers, 'customers')}
        recordType="Customer"
        startLoading={this.startLoading}
        stopLoading={this.stopLoading}
      />
    )
  }

  loadData = (func, name) => {
    this.startLoading();
    this.getRecordsData(func, name).then(d => {
      this.stopLoading();
    });
  }

  componentDidMount() {
    this.startLoading();
    Promise.all([
      this.getRecordsData(getSafetyWears, 'safetyWears'),
      this.getRecordsData(getCustomers, 'customers'),
      this.getRecordsData(getProducts, 'products'),
      this.getRecordsData(getCategories, 'categories'),
      this.getRecordsData(getMarkets, 'markets'),
      this.getRecordsData(getSizes, 'sizes'),
    ]).then(datas => {
      this.stopLoading();
    });
  }

  renderCardGrid(contents) {
    return contents.map(
      (t, i) => (<Row key={`${i}_key`}>{ t }</Row>));
  }

  renderCustomerGrid(contents) {
    return contents.map((c, i) => (<Row key={i}><a href={`/customer_sheet/${c.id}`} target="blank">{c.businessName}</a></Row>));
  }

  renderCustomerSheet = ({ match }) => {
    const { customers } = this.state;
    const customer_id = match.params.customer_id;
    const customer = customers.find(c => c.id == customer_id);
    if(!customer) {
      return (<div />);
    }
    return (
      <CustomerSheet customer_id={customer_id} onReady={this.stopLoading} />
    );
  }

  renderDownloadLink() {
    if(window.location.pathname.split("/")[1] !== 'customer_sheet' || this.state.loading === true) {
      return null;
    }
    return (
      <Col span={4}>
        <Button onClick={this.download} disabled={this.state.loading}>
          Print
        </Button>
      </Col>
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
        <Route exact={true} path="/app" render={this.renderHome} key={3} />
      </div>
    )
  }

}

export default DistributorPage;
