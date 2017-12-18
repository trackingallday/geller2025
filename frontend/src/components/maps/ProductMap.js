import React, { Component } from 'react';
import ReactMapboxGl, { Layer, Popup, Feature } from "react-mapbox-gl";
import { Select, Row, Col } from 'antd';
import { getProductsMap } from '../../util/DjangoApi';
import imgsrc from '../image';


const Option = Select.Option;


function debounce(func, wait, immediate) {
	var timeout;
	return function() {
		var context = this, args = arguments;
		var later = function() {
			timeout = null;
			if (!immediate) func.apply(context, args);
		};
		var callNow = immediate && !timeout;
		clearTimeout(timeout);
		timeout = setTimeout(later, wait);
		if (callNow) func.apply(context, args);
	};
};

const Map = ReactMapboxGl({
  accessToken: "pk.eyJ1IjoiY2hlbXNhcHAiLCJhIjoiY2pheWdzNjd6MTJnbDMzczczbG92ZG15ayJ9.sqO7Za5EYpuhj6REKyneFA",
});

const containerStyle= {
  height: "100vh",
  width: "100vw"
};

const img = new Image(20, 20);
img.src = imgsrc;

const images = ['londonCycle', img ];

//const mapStyUri = "mapbox://styles/mapbox/streets-v9";
const mapStyUri = "mapbox://styles/chemsapp/cjb6ybqof16v72qmi0vw6mzqg";

export default class ProductMap extends Component {

  state = {
    products: [],
    selectedProducts: [],
    selectedCustomers: [],
    initialProps: {
      center: [173.230989, -41.2849619],
      zoom:[5],
    }
  }

  markerHover = ({ map, feature, lngLat }, customer) => {
    this.setState({
      selectedCustomer: customer,
    });
  };

  markerOut =  ({ map, feature, lngLat }, customer) => {
    if(this.state.selectedCustomer){
      this.setState({
        selectedCustomer: null,
      });
    }
  };

  componentDidMount() {
    getProductsMap((data) => {
      const customers = this.getCustomers(data);
      this.setState({
        products: data,
        selectedProducts: data,
        selectedCustomers: customers,
        selectedCustomer: null,
      });
    });
  }

  getCustomers(products) {
    const customers = {};
    products.forEach((p) => {
      p.customers.forEach((c) => {
        if(c.geocodingDetail) {
          c.geo = JSON.parse(c.geocodingDetail);
          customers[c.id] = c;
        }
      });
    });
    return Object.values(customers);
  }

  onProductSelectChange = (productIds) => {
    if(!productIds.length) {
      this.setState({
        selectedProducts: this.state.products,
        selectedCustomers: this.getCustomers(this.state.products),
      });
    } else {
      const selectedProducts = this.state.products.filter((p) => productIds.includes(p.id));
      const customers = this.getCustomers(selectedProducts);
      const selectedCustomers = customers.filter((c) => productIds.every(pId => c.productIds.includes(pId)));
      this.setState({
        selectedProducts,
        selectedCustomers,
      });
    }
  }

  renderProductMenu = () => {
    const opts = this.state.products.map((p, i) => (
      <Option key={i} value={p.id}>{ p.name }</Option>
    ));
    return (
      <Select
        mode="multiple"
        style={{ width: '90%' }}
        placeholder="Select Products"
        onChange={ this.onProductSelectChange }
      >
       { opts }
      </Select>
    );
  }

  renderCustomerMenu = (customerIds) => {
    const opts = this.state.customers.map((p, i) => (
      <Option key={i} value={p.id}>{ p.businessName }</Option>
    ));
    return (
      <Select
        mode="multiple"
        style={{ width: '90%' }}
        placeholder="Select Products"
        onChange={ this.onProductSelectChange }
      >
       { opts }
      </Select>
    );
  }

  renderSelectedCustomers() {
    return this.state.selectedCustomers.map((c, i) => {
      const mousIn = debounce((args) => this.markerHover(args, c));
      const mouseOut = debounce((args) => this.markerOut(args, c));
      return (
        <Feature
          key={i}
          coordinates={c.geo.geometry.coordinates}
          onClick={mousIn}
          onMouseLeave={mouseOut}
        />
      );
    });
  }

  renderPopup = () => {
    const cust = this.state.selectedCustomer;
    if(!cust) return null;
    const products = cust.products.map((p, i) => (<span key={i}>{ p }</span>));
    const distributors = cust.distributors.map((p, i) => (<span key={`dis${i}`}>{ p.businessName }</span>));

    return (
      <Popup
        coordinates={ cust.geo.geometry.coordinates }
      >
        <h3>{ cust.businessName }</h3>
        <p>{ cust.geo.place_name }</p>
        <p>products: { products }</p>
        <p>distributor: { distributors }</p>
      </Popup>
    );
  }

  render() {
    const features = this.renderSelectedCustomers();
    return (
      <div>
        <Row style={{padding: 10}}>
          <Col span={12}>
             <p>Filter By Products</p>
             { this.renderProductMenu() }
          </Col>
      </Row>
        <Map style={mapStyUri} containerStyle={containerStyle}
          { ...this.state.initialProps }
        >
          <Layer
            type="symbol"
            id="marker"
            layout={{ "icon-image": "londonCycle", "icon-allow-overlap": false, "icon-padding": 0 }}
            images={images}
          >
            { features }
          </Layer>
          { this.renderPopup() }
        </Map>
      </div>
    );
  }
}
