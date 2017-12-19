import React, { Component } from 'react';
import { Layout, Row } from 'antd';
import Loadable from 'react-loading-overlay';

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
