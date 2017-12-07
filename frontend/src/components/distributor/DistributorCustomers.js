import React, { Component } from 'react';
import { Modal, Button, Row, Col  } from 'antd';
import axios from 'axios';
import serverUrl from '../../constants/serverUrl';
import CustomersTable from './CustomersTable';

const data = [{"phoneNumber":"235235325",
  "first_name":"aliens","last_name":"inspace","email":"aliens@space.ship",
  "cellPhoneNumber":"2345234235","businessName":"b name","lat":"23.00000000","lon":"23.00000000",
  "products":["SpraynWipe - avondale chemical bros and company","SpraynWipe2 - smo bros"]}];

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
    console.log(axios.defaults.headers);
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
