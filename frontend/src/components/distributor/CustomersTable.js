import React, { Component } from 'react';
import { Table, Input, Button, Icon } from 'antd';

export default class CustomersTable extends Component {

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
    }, {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    }, {
      title: 'Address',
      dataIndex: 'address',
      key: 'address',
      filters: [{
        text: 'Dunedin',
        value: 'Dunedin',
      }, {
        text: 'Christchurch',
        value: 'Christchurch',
      }],
      onFilter: (value, record) => record.address.indexOf(value) === 0,
    }, {
      title: 'Cell Ph',
      dataIndex: 'cellPhoneNumber',
      key: 'cellPhoneNumber',
    }, {
      title: 'Phone',
      dataIndex: 'phoneNumber',
      key: 'phoneNumber',
    }, {
      title: 'Contact Name',
      dataIndex: 'first_name',
      key: 'first_name',
      render: (value, record) => `${record.first_name} ${record.last_name}`,
    }, {
      title: 'Products',
      dataIndex: 'products',
      key: 'products',
      render: (value, record) => value.slice(0, 15) + "...",
    },
    {
      title: 'Edit',
      key: 'operation',
      width: 80,
      render: () => <a href="#">edit</a>,
    },
    ];
    const data = filtered ? filteredData : this.props.data;
    return <Table columns={columns} dataSource={data} />;
  }

 }
