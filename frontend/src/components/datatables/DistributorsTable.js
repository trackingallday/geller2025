import React, { Component } from 'react';
import { Table, Input, Icon, Row, Col } from 'antd';
import CustomersTable from './CustomersTable';
import { alphabetSort } from '../../util/Sorter';

const distributorDetailList = [
  [ 'Name', 'businessName'],
  [ 'Contact First Name', 'first_name' ],
  [ 'Contact Last Name', 'last_name'],
  [ 'Email','email'], ['Address', 'address'], ['phoneNumber', 'phoneNumber'],
  [ 'Cell Phone', 'cellPhoneNumber'],
];


const originalState = {
  filterDropdownVisible: false,
  data: [],
  products: [],
  productsFilterVisible: false,
  filteredData: [],
  searchText: '',
  filtered: false,
};


export default class DistributorsTable extends CustomersTable {

  constructor(props) {
    super(props);
    this.expandedRowRender = this.expandedRowRender.bind(this);
  }

  state = originalState

  componentDidMount() {
    this.setState(originalState);
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
      filteredData: this.searchRecords('businessName', searchText, this.props.data),
    });
  }

  getColumns = () => {
    const { searchText, filterDropdownVisible, filtered } = this.state;
    const filterInput = this.renderFilterInput(searchText, this.onInputChange, this.onSearch);

    const columns = [{
      title: 'Name',
      dataIndex: 'businessName',
      key: 'businessName',
      filterDropdown: filterInput,
      filterIcon: <Icon type="search" style={{ color: filtered ? '#108ee9' : '#aaa' }} />,
      filterDropdownVisible: filterDropdownVisible,
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
    return columns;
  }

  renderDetail = (record) => {
     return distributorDetailList.map((def, i) => {
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

 }
