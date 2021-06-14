import React from 'react';
import { Route, NavLink } from 'react-router-dom';
import { Menu, Row, Col, Icon, } from 'antd';
import DistributorPage from './Distributor';
import styles from '../../styles';
import NewDistributorForm from '../forms/NewDistributorForm';
import EditDistributorForm from '../forms/EditDistributorForm';
import ProductMap from '../maps/ProductMap';
import DistributorsTable from '../datatables/DistributorsTable';
import RecordAdmin from '../common/RecordAdmin';
import { getDistributors, getSafetyWears,
  getCustomers, getMarkets, getSizes, getProducts, getCategories } from '../../util/DjangoApi';

class AdminPage extends DistributorPage {

    getDistributors = (callback) => {
      this.getDataAndLoading(callback, getDistributors);
    }

    componentDidMount() {
      this.startLoading();
      Promise.all([
        this.getRecordsData(getSafetyWears, 'safetyWears'),
        this.getRecordsData(getCustomers, 'customers'),
        this.getRecordsData(getProducts, 'products'),
        this.getRecordsData(getDistributors, 'distributors'),
        this.getRecordsData(getMarkets, 'markets'),
        this.getRecordsData(getCategories, 'categories'),
        this.getRecordsData(getSizes, 'sizes'),
      ]).then(datas => {
        this.stopLoading();
      });
    }


    renderDistributors = () => {
      return (
        <RecordAdmin
          newForm={NewDistributorForm}
          editForm={EditDistributorForm}
          recordsTable={DistributorsTable}
          records={this.state.distributors}
          getDataFunc={() => this.loadData(getDistributors, 'distributors')}
          recordType="Distributor"
          startLoading={this.startLoading}
          stopLoading={this.stopLoading}
        />
      );
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
            <NavLink exact to="/app" label="Home">Home</NavLink>
          </Menu.Item>
          <Menu.Item key="/distributors">
            <NavLink exact to="/distributors" label="Distributors">Distributors</NavLink>
          </Menu.Item>
          <Menu.Item key="/customers">
            <NavLink exact to="/customers" label="Customers">Customers</NavLink>
          </Menu.Item>
          <Menu.Item key="/products">
            <NavLink exact to="/products" label="Products">Products</NavLink>
          </Menu.Item>
          <Menu.Item key="/maps">
            <NavLink exact to="/maps" label="Maps">Maps</NavLink>
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

  renderContent() {
    return (
      <div style={styles.container}>
        <Route exact={true} path="/customers" render={this.renderDistributorCustomers} key={1} />
        <Route exact={true} path="/products" render={this.renderDistributorProducts} key={2} />
        <Route exact={true} path="/distributors" render={this.renderDistributors} key={9} />
        <Route exact={true} path="/" render={this.renderHome} key={3} />
        <Route exact={true} path="/app" render={this.renderHome} key={39} />
        <Route exact={true} path="/maps" component={ProductMap} key={4} />
        <Route path="/customer_sheet/:customer_id" render={this.renderCustomerSheet} key={8} />
      </div>
    )
  }

}

export default AdminPage;
