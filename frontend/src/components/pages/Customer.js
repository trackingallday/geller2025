import React, { Component } from 'react';
import { Row, Col, Layout, Button, Icon } from 'antd';
import { getProducts, getSafetyWears, getUserDetails } from '../../util/DjangoApi';
import QRCode from 'qrcode.react';
import BasePage from './BasePage';
import Loadable from 'react-loading-overlay';
import styles from '../../styles';
import ReactDOMServer from 'react-dom/server';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import moment from 'moment';
import CustomerSheet from '../common/CustomerSheet';


const { Content, Header, Footer } = Layout;


const url = 'http://127.0.0.1:8000';


class CutomerPage extends BasePage {

  state = {
    user: null,
    products: null,
    safetyWears: null,
  }

  componentDidMount() {
    getSafetyWears((data) => {
      this.setState({ safetyWears: data });
    });
    getProducts((data) => {
      this.setState({ products: data });
    });
    getUserDetails((data) => {
      this.setState({ user: data });
    });
  }

  download = () => {
    const { products, safetyWears } = this.state;
    const { user } = this.props;
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

  render() {
    const { products, safetyWears } = this.state;
    const { user } = this.props;
    const { profile } = user;
    const loaded = !!(user && products && safetyWears);

    return (
      <Loadable
        active={!loaded }
        color={'#fea3aa'}
        spinner
        text={'Loading ...'}
        zIndex={9001}
        spinnerSize={'200px'}
        background={'rgba(255,255,255,0.7)'}
        animate={true}
      >
        <Layout className="layout">
          <Header>
            <Row>
              <Col span={4}>
                <Button onClick={this.download}>
                  Print
                </Button>
              </Col>
              <Col span={20}>
                <Row type={'flex'} justify='end'>
                  <Col>
                    <a onClick={this.logout} style={{ color: '#fff' }}>
                      <Icon type="user-delete" style={{ fontSize: 20}} />
                      <span style={{ fontSize: 14}}>Logout</span>
                    </a>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Header>
          <Content>
            { loaded && <CustomerSheet user={user} products={products} safetyWears={safetyWears} /> }
          </Content>
        </Layout>
      </Loadable>
    );
  }

}

export default CutomerPage
