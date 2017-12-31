import React from 'react';
import { Row, Col, Layout, Button, Icon } from 'antd';
import { getProducts, getSafetyWears, getUserDetails } from '../../util/DjangoApi';
import BasePage from './BasePage';
import Loadable from 'react-loading-overlay';
import CustomerSheet from '../common/CustomerSheet';


const { Content, Header } = Layout;


class CutomerPage extends BasePage {

  componentDidMount() {
    this.setState({ loading: true });
  }

  renderHeader = () => {
    const button = !this.state.loading && (
      <Button onClick={this.download}>
        Print
      </Button>
    );
    return (
      <Header>
        <Row>
          <Col span={4}>
            { button }
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
    );
  }

  renderContent() {
    return (<CustomerSheet onReady={this.stopLoading} />);
  }

}

export default CutomerPage
