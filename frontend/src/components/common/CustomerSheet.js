import React, { Component } from 'react';
import { Row, Col } from 'antd';
import { getCustomerSheet, postCustomerSheet } from '../../util/DjangoApi';
import moment from 'moment';
import styles from '../../styles';
import URI from '../../constants/serverUrl';

 export default class CustomerSheet extends Component {

   state = {
     data: null,
   }

   setData = ({ data }) => {
     console.log(data);
     const { products, distributor } = data;
     this.setState({
        customer: data,
        distributor,
        products,
     });
     this.props.onReady()
   }

  componentDidMount() {
    const { customer_id, user } = this.props;
    if(customer_id) {
      postCustomerSheet(customer_id, this.setData);
    } else {
      getCustomerSheet(this.setData);
    }
  }

  getSafetyIcon(imageLink) {
    if (imageLink.slice(0, 1) == '/') {
      return URI + imageLink
    }

    return imageLink
  }

  renderSafetyWears = (product) => {
    if(!product.safetyWears){
      return null;
    }
    return product.safetyWears.map((sf, i) => {
      return (
        <Col span={3} key={sf.id+"-"+i} style={{margin: '0 4px 0 4px'}}>
          <img
            crossOrigin='anonymous'
            width='18px'
            src={this.getSafetyIcon(sf.imageLink)}
            key={`${sf.id}-${product.id}`}
          />
        </Col>
      );
    });
  }

  renderProduct = (product, index) => {
    const {
      primaryImageLink,
      secondaryImageLink,
      name, brand, usageType, amountDesc,
      directions,
    } = product
    const textStyle = {
      fontFamily: 'Aktiv Grotesk, sans-serif',
      fontSize: '11px',
      lineHeight: 1.2,
      width: '100%',
      display: 'inline-block',
      margin: '0',
    }
    const titleStyle = Object.assign({}, { display: 'inline-block', fontFamily: 'Aktiv Grotesk Regular, sans-serif', fontWeight: '700', fontSize: '13px', lineHeight: 1.8, });
    const midStyle = Object.assign(textStyle, { fontWeight: '500', fontSize: '11px', width: '100%', textOverflow: 'ellipsis', overflow: 'hidden' });
    const bottomStyle = Object.assign(textStyle, { fontWeight: '400', fontSize: '11px', whiteSpace:'wrap-word'});

    const titleRowStyle = { }
    const midRowStyle = { width: '100%', whiteSpace: 'nowrap' };
    const bottomRowStyle = { minHeight: '50px', paddingBottom: '10px' }

    return (
      <div className="toprint-item" key={index} style={{'minHeight': '130px', borderWidth: '0px 0px 0.5px 0px', borderStyle: 'solid', margin: '6px 0px 3px 0px'}}>
        <Row type="flex" justify="start">
          <Col span={3} align="middle">
            <img crossOrigin='anonymous' alt=""
              style={{ width: '100%' }}
              src={URI + primaryImageLink}
            />
          </Col>
          <Col span={4} align="middle">
            <img crossOrigin='anonymous' alt="" style={{ width: '100%', borderLeft: '4px solid #fff', borderRight: '5px solid #fff'}} src={URI + secondaryImageLink} />
          </Col>
          <Col span={13} style={{ paddingRight: '10px' }}>
            <Row style={titleRowStyle}>
              <span style={titleStyle}>{ `${brand} ${name}`}</span>
            </Row>
            <Row style={midRowStyle}>
              <span style={midStyle}>{usageType}</span>
            </Row>
            <Row style={midRowStyle}>
              <p style={midStyle}>{amountDesc}</p>
            </Row>
            <Row style={bottomRowStyle}>
              <span style={bottomStyle}>{ directions }</span>
            </Row>
          </Col>
          <Col span={4}>
            {product.sdsQrcode &&
              <Row>
                <Col span={24}>
                <span style={{ fontSize: '11px' }}>Download SDS</span>
                </Col>
              </Row>
            }
            {product.sdsQrcode &&
              <Row>
                <Col span={24}>
                  <img width={100} src={product.sdsQrcode} />
                </Col>
              </Row>
            }
            {product.safetyWears.length > 0 &&
              <Row>
                <Col span={24}>
                  <span style={{ fontSize: '11px' }}>Required PPE</span>
                </Col>
              </Row>
            }
            <Row>
              <Col span={24} style={{ marginBottom: '10px' }}>
                { this.renderSafetyWears(product)}
              </Col>
            </Row>
          </Col>
        </Row>
      </div>
    )
  }

  renderHeader = () => {
    const { customer, distributor } = this.state;
    const date = moment().add('years', 1).format("DD MMMM YYYY");
    return (
      <Row type="flex" justify="start" style={{ borderWidth: '0px 0px 0.5px 0px', borderStyle: 'solid',}}>
        <Col span="15">
          <Row style={{fontSize: '18px', paddingBottom: '10px'}}>
            <span>Chemical Safety Procedures</span>
          </Row>
          <Row style={{fontSize: '18px', paddingBottom: '6px'}}>
            <span>{ customer.businessName }</span>
          </Row>
          <Row style={{fontSize: '13px', paddingBottom: '6px'}}>
            <span>{ distributor.businessName}</span>
          </Row>
          <Row style={{fontSize: '13px', paddingBottom: '6px'}}>
            <span>{ `Re-order: ${distributor.phoneNumber}`}</span>
          </Row>
          <Row style={{fontSize: '11px', paddingBottom: '6px'}}>
            <span>{ `Vaild until:  ${date}` }</span>
          </Row>
        </Col>
        <Col span="9">
          <Row style={{paddingBottom: '10px'}}>
            <img alt="" crossOrigin='anonymous' style={{ width: '100%' }} src={URI + distributor.primaryImageLink} />
          </Row>
        </Col>
      </Row>
    )
  }

  render() {

    const { products } = this.state;
    if(!products) {
      return <div />
    }

    return (
      <div style={styles.a4Page} id={"toprint"}>
        <div id="toprint-header">
          { this.renderHeader()}
        </div>
        <div>
          { products.map(this.renderProduct) }
        </div>
      </div>
    );
  }

}
