import React, { Component } from 'react';
import { Row, Col } from 'antd';
import moment from 'moment';
import styles from '../../styles';


 export default class CustomerSheet extends Component {

  renderSafetyWears = (product) => {
    if(!product.safetyWears){
      return null;
    }
    return product.safetyWears.map((id, i) => {
      const sf = this.props.safetyWears.find((s) => s.id === id);
      return (
        <Col span={3} key={id+"-"+i} style={{margin: '0 4px 0 4px'}}>
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
    const midStyle = Object.assign({}, textStyle, { fontWeight: '600', fontSize: '11px' });
    const bottomStyle = Object.assign({}, textStyle, { fontWeight: '400', fontSize: '11px', height: '40px', whiteSpace:'wrap-word'});

    const titleRowStyle = { height: '20px'}
    const midRowStyle = { height: '20px', top: '-10px' };
    const bottomRowStyle = { height: '50px', top: '-7px'}

    return (
      <div key={index} style={{height: '145px', borderWidth: '1px 0px 0px 0px', borderStyle: 'solid', paddingTop: '4px'}}>
        <Row type="flex" justify="start">
          <Col span={3}>
              <img crossOrigin='anonymous' alt=""
                style={{ width: '100%', height: 100 }}
                src={primaryImageLink}
              />
          </Col>
          <Col span={4}>
            <img crossOrigin='anonymous' alt="" style={{ width: '100%', height: 100, borderLeft: '4px solid #fff', borderRight: '5px solid #fff' }} src={secondaryImageLink} />
          </Col>
          <Col span={13}>
            <Row style={titleRowStyle}>
              <span style={titleStyle}>{ `${brand} ${name}`}</span>
            </Row>
            <Row style={midRowStyle}>
              <span style={midStyle}>{usageType}</span>
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
                <img width={90} src={product.sdsQrcode} />
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
    const user = this.props.user;
    const profile = user.profile;
    return (
      <Row type="flex" justify="start" style={{}}>
        <Col span="18">
          <Row style={{fontSize: '18px', wordSpacing: '8px'}}>
            <span>Chemical Cleaning Safety Procedures</span>
          </Row>
          <Row style={{fontSize: '16px', wordSpacing: '8px' }}>
            <span>{ profile.businessName }</span>
          </Row>
          <Row style={{fontSize: '14px', paddingBottom: '10px', wordSpacing: '8px'}}>
            <span>{ `${moment().format("DD MMMM YYYY")}` }</span>
          </Row>
        </Col>
        <Col span="6">
          <Row>
            <img alt="" crossOrigin='anonymous' style={{ width: '140px' }} src={"https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/IBM_logo.svg/1200px-IBM_logo.svg.png"} />
          </Row>
        </Col>
      </Row>
    )
  }

  render() {

    return (
      <div style={styles.a4Page} id={"toprint"}>
        <div>
          { this.renderHeader()}
        </div>
        <div>
          { this.props.products.map(this.renderProduct) }
        </div>
      </div>
    );
  }

}
