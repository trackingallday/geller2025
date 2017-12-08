import React, { Component } from 'react';
import { Table, Input, Button, Icon, Row, Col, Card } from 'antd';
import QRCode from 'qrcode.react';


const { Meta } = Card;
const url = 'http://127.0.0.1:8000';

const productDetailList = [
  [ 'Name', 'name'],
  [ 'Usage', 'usageType' ],
  ['Amount', 'amountDesc'],
  [ 'Instructions','instructions'], ['Code', 'productCode'], ['Brand', 'brand'],
  [ 'Saftey Wear', 'safetyWears'], ['Customers', 'customers'],
];

const renderProductDetail = (record) => {
   return productDetailList.map((def, i) => {
    console.log(def, record, record[def[1]], def[1]);
    return (
      <Row key={i}>
        <Col span={4}>
          {def[0]}
        </Col>
        <Col span={20}>
          {record[def[1]]}
        </Col>
      </Row>
    );
  });
}


const expandedRowRender = (record) => {

  const detail = renderProductDetail(record);
  return (
    <div>
      <Row type="flex" justify="start">
        <Col span={6}>
            <Card
              hoverable
              style={{ width: 180 }}
              cover={<img alt="image 2" src={record.primaryImageLink} />}
            >
              <Meta
                title={record.name}
                description={ record.brand }
              />
            </Card>
            <Card
              hoverable
              style={{ width: 180 }}
              cover={<img alt="image 2" src={record.secondaryImageLink} />}
            >
            </Card>
        </Col>
        <Col span={18}>
          <div>
            { detail }
            <Row>
              <Col span={4}>
                SDS Link
              </Col>
              <Col span={20}>
                <Row>
                  {url}{record.infoSheet}
                </Row>
                <Row>
                  <QRCode value={`${url}${record.sdsSheet}`} />
                </Row>
              </Col>
            </Row>
            <Row>
              <Col span={4}>
                Info Sheet
              </Col>
              <Col span={20}>
                <Row>
                  {url}{record.infoSheet}
                </Row>
                <Row>
                  <QRCode value={`${url}${record.infoSheet}`} />
                </Row>
              </Col>
            </Row>
            <div>
            </div>
            <div>
            </div>
          </div>
        </Col>
      </Row>
    </div>
  );
}


export default class ProductsTable extends Component {

  state = {
    filterDropdownVisible: false,
    data: [],
    filteredData: [],
    searchText: '',
    filtered: false,
  };

  onInputChange = (e) => {
    this.setState({ searchText: e.target.value });
  }

  onSearch = () => {
    const { searchText } = this.state;
    const reg = new RegExp(searchText, 'gi');
    this.setState({
      filterDropdownVisible: false,
      filtered: !!searchText,
      filteredData: this.props.data.map((record) => {
        const match = record.businessName.match(reg);
        if (!match) {
          return null;
        }
        return {
          ...record,
          name: (
            <span>
              {record.businessName.split(reg).map((text, i) => (
                i > 0 ? [<span className="highlight">{match[0]}</span>, text] : text
              ))}
            </span>
          ),
        };
      }).filter(record => !!record),
    });
  }

  render() {
    const { filteredData, filtered } = this.state;
    const filterInput = (
      <div className="custom-filter-dropdown">
        <Input
          ref={ele => this.searchInput = ele}
          placeholder="Search"
          value={this.state.searchText}
          onChange={this.onInputChange}
          onPressEnter={this.onSearch}
        />
        <Button type="primary" onClick={this.onSearch}>Search</Button>
      </div>
    );

    const columns = [{
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      filterDropdown: filterInput,
      filterIcon: <Icon type="smile-o" style={{ color: filtered ? '#108ee9' : '#aaa' }} />,
      filterDropdownVisible: this.state.filterDropdownVisible,
      onFilterDropdownVisibleChange: (visible) => {
        this.setState({
          filterDropdownVisible: visible,
        }, () => this.searchInput && this.searchInput.focus());
      },
    }, {
      title: 'Brand',
      dataIndex: 'brand',
      key: 'brand',
    },
    {
      title: 'Info',
      key: 'infoSheet',
      dataIndex: 'infoSheet',
      render: (value, record) => <a target="blank" href={`${url}${record.infoSheet}`}>link</a>,
    },
    {
      title: 'SDS',
      key: 'sdsSheet',
      dataIndex: 'sdsSheet',
      render: (value, record) => <a target="blank" href={`${url}${record.sdsSheet}`}>link</a>,
    },
    {
      title: 'Edit',
      key: 'operation',
      width: 80,
      render: () => <a href="#">edit</a>,
    },
    ];
    const data = filtered ? filteredData : this.props.data;
    return <Table columns={columns} dataSource={data} expandedRowRender={expandedRowRender} onExpand={this.onTableExpand} />;
  }

 }
