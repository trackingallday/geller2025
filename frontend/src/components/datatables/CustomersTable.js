import React, { Component } from 'react';
import { Table, Input, Button, Icon, Row, Col } from 'antd';
import { getProducts } from '../../util/DjangoApi';
import { alphabetSort } from '../../util/Sorter';

const customerDetailList = [
  [ 'Name', 'businessName'],
  [ 'Contact First Name', 'first_name' ],
  [ 'Contact Last Name', 'last_name'],
  [ 'Email','email'], ['Address', 'address'], ['phoneNumber', 'phoneNumber'],
  [ 'Cell Phone', 'cellPhoneNumber'], ['Products', 'products'],
];


const renderCustomerDetail = (record) => {
   return customerDetailList.map((def, i) => {
    return (
      <Row key={i}>
        <Col span={4}>
          {def[0]}
        </Col>
        <Col span={20}>
          <span style={{wordWrap: 'break-word'}}>
            {record[def[1]]}
          </span>
        </Col>
      </Row>
    );
  });
}


const expandedRowRender = (record) => {

  const detail = renderCustomerDetail(record);

  return (
    <div>
      <Row type="flex" justify="start">
        <Col span={24}>
          { detail }
        </Col>
      </Row>
    </div>
  );
}


export default class CustomersTable extends Component {

  state = {
    filterDropdownVisible: false,
    data: [],
    products: [],
    productsFilterVisible: false,
    filteredData: [],
    searchText: '',
    filtered: false,
  };

  componentDidMount() {
    getProducts( (products) => {
      this.setState({ products: products.map(p => ({ text: p.name, value: p.name })) });
    });
  }

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
      dataIndex: 'businessName',
      key: 'businessName',
      filterDropdown: filterInput,
      filterIcon: <Icon type="smile-o" style={{ color: filtered ? '#108ee9' : '#aaa' }} />,
      filterDropdownVisible: this.state.filterDropdownVisible,
      onFilterDropdownVisibleChange: (visible) => {
        this.setState({
          filterDropdownVisible: visible,
        }, () => this.searchInput && this.searchInput.focus());
      },
      defaultSortOrder: 'descend',
      sorter: (a, b) => alphabetSort(a.businessName, b.businessName),
    }, {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      defaultSortOrder: 'descend',
      sorter: (a, b) => alphabetSort(a.email, b.email),
    }, {
      title: 'First Name',
      dataIndex: 'first_name',
      key: 'first_name',
      defaultSortOrder: 'descend',
      sorter: (a, b) => alphabetSort(a.first_name, b.first_name),
    },{
      title: 'Last Name',
      dataIndex: 'last_name',
      key: 'last_name',
      defaultSortOrder: 'descend',
      sorter: (a, b) => alphabetSort(a.last_name, b.last_name),
    },{
      title: 'Products',
      dataIndex: 'products',
      key: 'products',
      filters: this.state.products,
      onFilter: (value, record) => record.products.find((p) => p.trim() === value.trim()),
      render: (value, record) => value.slice(0, 30) + "...",
    },
    {
      title: 'Edit',
      key: 'operation',
      width: 80,
      render: (value, record) => (
        <a onClick={() => this.props.onEditClick(value, record)}>
          edit
        </a>
      ),
    },
    ];
    const data = filtered ? filteredData : this.props.data;
    return <Table columns={columns} dataSource={data} expandedRowRender={expandedRowRender} onExpand={this.onTableExpand} />;
  }

 }
