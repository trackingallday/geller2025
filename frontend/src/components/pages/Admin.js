import React from 'react';
import { Route, NavLink } from 'react-router-dom';
import { Menu, Row, Col, Icon, } from 'antd';
import DistributorPage from './Distributor';
import styles from '../../styles';
import ProductMap from '../maps/ProductMap';
import ReactDOMServer from 'react-dom/server';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import moment from 'moment';
import CustomerSheet from '../common/CustomerSheet';

class AdminPage extends DistributorPage {

  download = () => {
    const { products, safetyWears } = this.state;
    const { user } = this.props;
    if(! (products && products.length && user && safetyWears && safetyWears.length)) {
      return null;
    }
    const markup = ReactDOMServer.renderToStaticMarkup(
      <CustomerSheet
        user={user} products={products} safetyWears={safetyWears}
      />
    );

    html2canvas(document.getElementById('toprint'), { useCORS: true }).then((canvas) => {
      const dataUrl = canvas.toDataURL("image/png", 1.0);
      var doc = new jsPDF('p', 'mm', [canvas.height, canvas.width]);
      doc.addImage(dataUrl, 'PNG', 0, 0, canvas.width, canvas.height);
      doc.save();
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
        <Route exact={true} path="/" render={this.renderHome} key={3} />
        <Route exact={true} path="/maps" component={ProductMap} key={4} />
      <Route path="/customer_sheet/:customer_id" render={this.renderCustomerSheet} key={8} />
      </div>
    )
  }

}

export default AdminPage;
