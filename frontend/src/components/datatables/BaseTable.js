import React, { Component } from 'react';
import { Table, Input, Button, Row, Col } from 'antd';


const FilterInput = ({ value, onChange, onSearch }) => (
  <div className="custom-filter-dropdown" style={{ padding: 5 }}>
    <Input
    style={{ marginBottom: 5 }}
      ref={ele => this.searchInput = ele}
      placeholder="Search"
      value={value}
      onChange={onChange}
      onPressEnter={onSearch}
    />
    <Button type="primary" onClick={onSearch}>Search</Button>
  </div>
);


export default class BaseTable extends Component {

  renderFilterInput(value, onChange, onSearch) {
    return (
      <FilterInput
        value={value}
        onChange={onChange}
        onSearch={onSearch}
      />
  );
  }

  searchRecord(record, key, searchText) {
    const reg = new RegExp(searchText, 'gi');

    if(!record[key]) {
      return null;
    }

    const match = record[key].match(reg);
    if (!match) {
      return null;
    }

    const words = record[key].split(reg).map(
      (text, i) => {
        if(i > 0) {
          return [<span key={'beep'} className="highlight">{match[0]}</span>, <span key={'boop'}>{ text }</span>];
        }
        return text;
      });

    return {
      ...record,
      [key]: (<span>{ words }</span>),
    };
  }

  searchRecords(key, searchText, data) {
    return data.map(
      (record) => this.searchRecord(record, key, searchText)).filter(
        record => !!record);
  }

  getColumns() {
    return [];
  }

  getData() {
    const { filteredData, filtered } = this.state;
    const data = filtered ? filteredData : this.props.data;
    return data;
  }

  expandedRowRender(record) {
    const detail = this.renderDetail(record);

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

  render() {
    const columns = this.getColumns();
    const data = this.getData();
    if(this.state.showEdit || this.state.showNew) {
      return  <Table columns={columns} dataSource={data} expandedRowRender={this.expandedRowRender} expandedRowKeys={[]} />;
    } else {
      return  <Table columns={columns} dataSource={data} expandedRowRender={this.expandedRowRender} />;
    }
  }

 }
