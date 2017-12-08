import React, { Component } from 'react';
import { Modal, Button, Row, Col  } from 'antd';
import axios from 'axios';
import serverUrl from '../../constants/serverUrl';
import ProductsTable from './ProductsTable';


export default class DistributorProducts extends Component {

  constructor() {
    super();
    this.state = {
      filterDropdownVisible: false,
      productsData: [],
      searchText: '',
      filtered: false,
    };
  }

  componentDidMount() {
    axios.defaults.headers.common['Authorization'] = this.props.token;
    axios.get(serverUrl + '/products_list/')
      .then((response) => {
        const products = response.data;
        this.setState({
          productsData: products.map((product, i) => Object.assign(product, { key: i })),
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
            <Button>New Product</Button>
          </Col>
        </Row>
        <Row>
          <Col span={24}>
            <ProductsTable data={this.state.productsData} />
          </Col>
        </Row>
      </div>
    );
  }

}
