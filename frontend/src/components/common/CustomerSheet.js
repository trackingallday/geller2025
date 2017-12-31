import React, { Component } from 'react';
import { Row, Col } from 'antd';
import { getCustomerSheet, postCustomerSheet } from '../../util/DjangoApi';
import moment from 'moment';
import styles from '../../styles';


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
            src={sf.imageLink}
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
      instructions,
    } = product
    const textStyle = {
      fontFamily: 'Helvetica',
      fontSize: '11px',
      wordWrap: 'elipsis',
      lineHeight: 1,
      whiteSpace: 'nowrap',
      textOverflow: 'ellipsis',
      width: '100%',
      display: 'inline-block',
      margin: '0 0 0 0',
    }
    const titleStyle = Object.assign({}, textStyle, { fontWeight: '800', fontSize: '11px', overflow: 'hidden' });
    const midStyle = Object.assign({}, textStyle, { fontWeight: '500', fontSize: '11px' });
    const bottomStyle = Object.assign({}, textStyle, { fontWeight: '400', fontSize: '11px', height: '40px', whiteSpace:'wrap-word'});

    const titleRowStyle = { height: '20px'}
    const midRowStyle = { height: '20px', top: '-10px', overflow: 'ellipsis' };
    const bottomRowStyle = { minHeight: '50px', top: '-7px', overflow: 'ellipsis' }

    return (
      <div key={index} style={{'minHeight': '130px', borderWidth: '0px 0px 0.5px 0px', borderStyle: 'solid', margin: '6px 0px 3px 0px'}}>
        <Row type="flex" justify="start">
          <Col span={3}>
              <img crossOrigin='anonymous' alt=""
                style={{ width: '100%', height: 125 }}
                src={primaryImageLink}
              />
          </Col>
          <Col span={4}>
            <img crossOrigin='anonymous' alt="" style={{ width: '100%', height: 125, borderLeft: '4px solid #fff', borderRight: '5px solid #fff' }} src={secondaryImageLink} />
          </Col>
          <Col span={13}>
            <Row style={titleRowStyle}>
              <span style={titleStyle}>{ `${brand} ${name}`}</span>
            </Row>
            <Row style={midRowStyle}>
              <span style={midStyle}>{usageType.substr(0, 50)}</span>
            </Row>
            <Row style={midRowStyle}>
              <span style={midStyle}>{amountDesc}</span>
            </Row>
            <Row style={bottomRowStyle}>
              <span style={bottomStyle}>{ instructions }</span>
            </Row>
          </Col>

          <Col span={4}>
            <Row>
              <Col span={24}>
                <img width={100} src={product.sdsQrcode} />
              </Col>
            </Row>
            <Row>
              <Col span={24}>
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
        <Col span="18">
          <Row style={{fontSize: '18px', wordSpacing: '5px'}}>
            <span>Chemical Cleaning Safety Procedures</span>
          </Row>
          <Row style={{fontSize: '18px', wordSpacing: '4px' }}>
            <span>{ customer.businessName }</span>
          </Row>
          <Row style={{fontSize: '13px', wordSpacing: '4px'}}>
            <span>{ distributor.businessName}</span>
          </Row>
          <Row style={{fontSize: '13px', wordSpacing: '6px'}}>
            <span>{ `Re-order: ${distributor.businessName} ${distributor.cellPhoneNumber} ${distributor.phoneNumber}`}</span>
          </Row>
          <Row style={{fontSize: '13px', paddingBottom: '10px', wordSpacing: '4px'}}>
            <span>{ `Vaild until: ${date}` }</span>
          </Row>
        </Col>
        <Col span="6">
          <Row>
            <img alt="" crossOrigin='anonymous' style={{ width: '160px' }} src={distributor.primaryImageLink} />
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
        <div>
          { this.renderHeader()}
        </div>
        <div>
          { products.map(this.renderProduct) }
        </div>
      </div>
    );
  }

}
