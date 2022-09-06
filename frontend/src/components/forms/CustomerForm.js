import React, { Component } from 'react';
import { Form, Input, Select } from 'antd';
import MapboxSearchInput from '../common/MapboxSearchInput';
import { formItemLayout } from '../../constants/tableLayout';

const FormItem = Form.Item;
const Option = Select.Option;


class CustomerForm extends Component {

  state = {
    confirmPasswordValue: false,
    autoCompleteResult: [],
    products: [],
    addressResult: null,
    submitting: false,
  };

  componentDidMount() {
    const { products } = this.props;
    this.setState({ products });
  }

  checkEmail = (rule, value, callback) => {
    if(/(.+)@(.+){2,}\.(.+){2,}/.test(value) !== true) {
      return callback('This email is invalid')
    }
    const { recordsData, recordToEdit } = this.props;
    if(recordsData.find(c => c.email === value) &! (recordToEdit && recordToEdit.email === value)) {
      return callback(`${value} has already been taken already`);
    }
    callback();
  }

  onAddressSelect = (result) => {
    const geo = JSON.parse(result);
    const { form } = this.props;
    const { place_name, place_type, text, properties } = geo;

    if(result === "initialValue") {
      form.setFieldsValue({
        address: this.getInitialValue('address'),
      });
    }

    form.setFieldsValue({
      address: place_name,
    });

    if(place_type && place_type.find((pt) => pt === 'poi')){
      form.setFieldsValue({
        businessName: text,
      });
    }
    if(properties.tel) {
      form.setFieldsValue({
        phone: properties.tel,
      });
    }
    this.setState({ addressResult: result });
  }

  getInitialValue(key) {
    if(!this.props.recordToEdit) {
      return;
    }
    return this.props.recordToEdit[key]
  }

  renderCommonFormFields() {
    const { getFieldDecorator } = this.props.form;

    return [
      (<FormItem {...formItemLayout} label="Contact First Name" key={1}>
        {getFieldDecorator('first_name',
         { initialValue: this.getInitialValue('first_name'),
           rules: [{ required: true, message: 'Please enter first name', }]})(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Contact Last Name" key={2}>
        {getFieldDecorator('last_name', {
          initialValue: this.getInitialValue('last_name')})(<Input />)}
      </FormItem>),
      (<FormItem
        {...formItemLayout}
        label="Email"
        key={3}
      >
        {getFieldDecorator('email', {
          initialValue: this.getInitialValue('email'),
          rules: [
            { required: true, message: 'Please input an email!'},
            { validator: this.checkEmail},
          ],
        })(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Address" help="Try typing the name of the business" key={4}>
        {getFieldDecorator('address', {
          initialValue: this.getInitialValue('address'),
          rules: [{ required: true, message: 'Please choose an address' }]})(
            <MapboxSearchInput onSelect={this.onAddressSelect} initialValue={this.getInitialValue('address')} />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Business Name" key={5}>
        {getFieldDecorator('businessName', {
          initialValue: this.getInitialValue('businessName'),
          rules: [{ required: true, message: 'Please input your username!' }]})(
            <Input name="businessName" />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Phone Number" key={6}>
        {getFieldDecorator('phoneNumber', {
          initialValue: this.getInitialValue('phoneNumber'),
          rules: [{ required: true, message: 'Please input a phone number!' }],})(
            <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Cell Phone Number" key={7}>
        {getFieldDecorator('cellPhoneNumber', {
          initialValue: this.getInitialValue('cellPhoneNumber')})(
          <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Products" key={8}>
        {getFieldDecorator('products',{
          initialValue: this.getInitialValue('products'),
          rules:[{required: true, message: 'Required!'}]})(
          <Select
            size="large"
            mode="multiple"
            placeholder="Please select"
            filterOption={(value, option) => {
              const { children: name } = option.props
              value = value.trim().replace(/[\\\.\+\*\?\^\$\[\]\(\)\{\}\/\'\#\:\!\=\|]/ig, "\\$&");
              const re = new RegExp(value.split(' ').join('.*'), 'i');
              return name.toLowerCase().search(re) >= 0;
            }}
         >
           { this.state.products.map((p, i) => {
              return (<Option key={`p${i}`} value={p.id}>{ p.name }</Option>);
            }) }
         </Select>)}
      </FormItem>),
    ];
  }

}

export default CustomerForm;
