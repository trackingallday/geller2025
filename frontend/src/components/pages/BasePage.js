import React, { Component } from 'react';
import { Layout, Row } from 'antd';
import Loadable from 'react-loading-overlay';
import ReactDOMServer from 'react-dom/server';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import moment from 'moment';
import CustomerSheet from '../common/CustomerSheet';

const { Header, Footer, Content } = Layout;

const colors = [
  '#ffb3ba', '#ffdfba', '#baffc9', '#bae1ff',
  '#e1f7d5', '#ffbdbd', '#c9c9ff', '#f1cbff',
  '#fea3aa', '#f8b88b', '#baed91', '#b2cefe', '#f2a2e8',
];

const getColor = () => colors[Math.floor(Math.random() * colors.length)];

class BasePage extends Component {

  state = {
    loading: false,
    color: getColor(),
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


  logout() {
    localStorage.setItem('token', null);
    window.location.replace("/");
  }

  stopLoading = () => {
    this.setState({
      loading: false,
    });
  }

  startLoading = () => {
    this.setState({
      loading: true,
      color: getColor(),
    });
  }

  renderMenu() {
    return (
      <Row type="flex" justify="start">
      </Row>
    );
  }


  renderFooter() {
    return (
      <Footer style={{ textAlign: 'center' }}>
        Cleaning Chemical Data Sheets & Safety Info
      </Footer>
    )
  }

  renderHeader() {
    return (
      <Header>
        <div className="logo">
        </div>
        { this.renderMenu() }
      </Header>
    )
  }

  renderContent() {
  }

  render() {
    return (
        <Layout className="layout">
          { this.renderHeader() }
          <Content>
            <Loadable
              active={this.state.loading}
              color={this.state.color}
              spinner
              text={'Loading ...'}
              zIndex={9001}
              spinnerSize={'200px'}
              background={'rgba(255,255,255,0.7)'}
              animate={true}
            >
              { this.renderContent() }
            </Loadable>
          </Content>
          { this.renderFooter() }
        </Layout>
    );
  }
}

export default BasePage;
