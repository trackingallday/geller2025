import React from 'react';
import { Icon, Row, Col, Card } from 'antd';
import BaseTable from './BaseTable';
import QRCode from 'qrcode.react';
import { alphabetSort } from '../../util/Sorter';
import url from '../../constants/serverUrl';


const { Meta } = Card;

const productDetailList = [
  [ 'Name', 'name'],
  [ 'Usage', 'usageType' ],
  ['Amount', 'amountDesc'],
  ['Application', 'application'],
  ['Properties', 'properties'],
  ['Description', 'description'],
  ['Sub Category', 'subCategory'],
  ['Markets', 'markets'],
  [ 'Directions','directions'], ['Code', 'productCode'], ['Brand', 'brand'],
  [ 'Saftey Wear', 'safetyWears'],
];

const renderProductDetail = (record) => {
   return productDetailList.map((def, i) => {
    return (
      <Row key={i}>
        <Col span={4}>
          {def[0]}
        </Col>
        <Col span={20}>
          <p>{record[def[1]]}</p>
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
              cover={<img alt="" src={url + record.primaryImageLink} />}
            >
              <Meta
                title={record.name}
                description={ record.brand }
              />
            </Card>
            {record.secondaryImageLink && (
            <Card
              hoverable
              style={{ width: 180 }}
              cover={<img alt="" src={url + record.secondaryImageLink} />}
            >
            </Card>
            )}
        </Col>
        <Col span={18}>
            { detail }
            <Row>
              <Col span={4}>
                SDS Link
              </Col>
              <Col span={20}>
                <Row>
                  <p>{url}{record.sdsSheet}</p>
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
                  <p>{url}{record.infoSheet}</p>
                </Row>
                <Row>
                  <QRCode value={`${url}${record.infoSheet}`} />
                </Row>
              </Col>
            </Row>
        </Col>
      </Row>
    </div>
  );
}


export default class ProductsTable extends BaseTable {

  state = {
    filterDropdownVisible: false,
    codeFilterDropdownVisible: false,
    data: [],
    filteredData: [],
    searchText: '',
    filtered: false,
    codeSearchText: '',
  };

  onInputChange = (e) => {
    this.setState({ searchText: e.target.value, codeSearchText: '', codeFilterDropdownVisible: false, filtered: false, });
  }

  onSearch = () => {
    const { searchText } = this.state;
    this.setState({
      filterDropdownVisible: true,
      filtered: !!searchText,
      filteredData: this.searchRecords('name', searchText, this.props.data),
    });
  }

  onCodeInputChange = (e) => {
    this.setState({ codeSearchText: e.target.value, searchText: '', filterDropdownVisible: false, filtered: false, });
  }

  onCodeSearch = () => {
    const { codeSearchText } = this.state;
    this.setState({
      codeFilterDropdownVisible: true,
      filtered: !!codeSearchText,
      filteredData: this.searchRecords('productCode', codeSearchText, this.props.data),
    });
  }

  getData = () => {
    const { filteredData, filtered, } = this.state;
    return filtered ? filteredData : this.props.data;
  }

  expandedRowRender = (record) => {
    return expandedRowRender(record, this.props.markets);
  }

  onEditClick = (value, record) => {
    this.props.onEditClick(value, record);
  }

  getLink = (value, record, attr) => {
     if(!typeof record[attr] === "string") {
       return <div />
     }
     else {
       return <a target="blank" href={`${url}${record[attr]}`}>link</a>
     }
  }

  getColumns = () => {
    const { searchText, filtered, codeSearchText } = this.state;
    const filterInput = this.renderFilterInput(searchText, this.onInputChange, this.onSearch);
    const codeFilterInput = this.renderFilterInput(codeSearchText, this.onCodeInputChange, this.onCodeSearch);
    return [{
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      filterDropdown: filterInput,
      filterIcon: <Icon type="search" style={{ color: filtered ? '#108ee9' : '#aaa' }} />,
      filterDropdownVisible: this.state.filterDropdownVisible,
      onFilterDropdownVisibleChange: (visible) => {
        this.setState({
          filterDropdownVisible: visible,
        }, () => this.searchInput && this.searchInput.focus());
      },
      sorter: (a, b) => alphabetSort(a.name, b.name),
    }, {
      title: 'Code',
      dataIndex: 'productCode',
      key: 'productCode',
      filterDropdown: codeFilterInput,
      filterIcon: <Icon type="search" style={{ color: filtered ? '#108ee9' : '#aaa' }} />,
      filterDropdownVisible: this.state.codeFilterDropdownVisible,
      onFilterDropdownVisibleChange: (visible) => {
        this.setState({
          codeFilterDropdownVisible: visible,
        }, () => this.searchInput && this.searchInput.focus());
      },
    }, {
      title: 'Brand',
      dataIndex: 'brand',
      key: 'brand',
      sorter: (a, b) => alphabetSort(a.brand, b.brand),
    },
    {
      title: 'Info',
      key: 'infoSheet',
      dataIndex: 'infoSheet',
      render: (value, record) => this.getLink(value, record, "infoSheet"),
    },
    {
      title: 'SDS',
      key: 'sdsSheet',
      dataIndex: 'sdsSheet',
      render:  (value, record) => this.getLink(value, record, "sdsSheet"),
    },
    {
      title: 'Edit',
      key: 'operation',
      width: 80,
      render: (value, record) => record.editable && <a onClick={ () => this.onEditClick(value, record) }>edit</a>,
    },
    ];
  }

 }
