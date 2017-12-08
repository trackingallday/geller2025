import React, { Component } from 'react';
import { Modal, Button, Row, Col  } from 'antd';
import axios from 'axios';
import serverUrl from '../../constants/serverUrl';
import CustomersTable from './CustomersTable';


export default class DistributorCustomers extends Component {

  constructor() {
    super();
    this.state = {
      filterDropdownVisible: false,
      customersData: [],
      searchText: '',
      filtered: false,
    };
  }

  componentDidMount() {
    axios.defaults.headers.common['Authorization'] = this.props.token;
    axios.get(serverUrl + '/customers_list/')
      .then((response) => {
        const customers = response.data.map((c, i) => {
          return Object.assign(c, c.user, { key: i });
        });
        console.log(customers)
        this.setState({
          customersData: customers,
        });
      }).catch((error) => {
        console.log(error);
      });
  }

  onMenuClick = ({ item, key, keyPath }) => {
    this.setState({ selectedMenuItem: key })
  }

  render = () => {
    return (
      <div>
        <Row type="flex" justify="end" style={{ paddingBottom: 12}}>
          <Col span={21}>
          </Col>
          <Col span={3}>
            <Button>New Customer</Button>
          </Col>
        </Row>
        <Row>
          <Col span={24}>
            <CustomersTable data={this.state.customersData} />
          </Col>
        </Row>
      </div>
    );
  }

}
