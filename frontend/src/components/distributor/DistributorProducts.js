import React, { Component } from 'react';
import { Modal, Button, Row, Col  } from 'antd';
import { getProducts } from '../../util/DjangoApi';
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
    getProducts( (products) => {
      this.setState({
        productsData: products.map((product, i) => Object.assign(product, { key: i })),
      });
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
