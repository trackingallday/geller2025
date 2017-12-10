import React, { Component } from 'react';
import { Form, Input, Select } from 'antd';
import MapboxSearchInput from './MapboxSearchInput';
import { getProducts } from '../../util/DjangoApi';


const FormItem = Form.Item;
const Option = Select.Option;

const formItemLayout = {
  labelCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  },
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 16 },
  },
};

class CustomerForm extends Component {

  state = {
    confirmPasswordValue: false,
    autoCompleteResult: [],
    products: [],
    addressResult: null,
  };

  componentDidMount() {
    getProducts( (products) => {
      this.setState({ products });
    });
  }

  handleConfirmBlur = (e) => {
    const value = e.target.value;
    this.setState({ confirmPasswordValue: this.state.confirmPasswordValue || !!value });
  }

  checkPassword = (rule, value, callback) => {
    const form = this.props.form;
    if (value && value !== form.getFieldValue('password')) {
      callback('Two passwords that you entered are not the same!');
    } else {
      if(value && value.length > 7) {
        callback();
        return;
      }
      callback("Password must be 8 characters or longer");
    }
  }

  checkEmail = (rule, value, callback) => {
    if(/(.+)@(.+){2,}\.(.+){2,}/.test(value) !== true) {
      return callback('This email is invalid')
    }
    if(this.props.customersData.find(c => c.email === value)) {
      return callback(`${value} has already been taken already`);
    }
    callback();
  }

  checkConfirm = (rule, value, callback) => {
    const form = this.props.form;
    if (value && this.state.confirmPasswordValue) {
      form.validateFields(['confirm'], { force: true });
    }
    callback();
  }

  onAddressSelect = (result) => {
    if(result === "initialValue") {
      form.setFieldsValue({
        address: this.getInitialValue('address'),
      });
    }
    const geo = JSON.parse(result);
    const { form } = this.props;
    const { place_name, place_type, text, properties } = geo;

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
    if(!this.props.customerToEdit) {
      return;
    }
    return this.props.customerToEdit[key]
  }

  renderCommonFormFields() {
    const { getFieldDecorator } = this.props.form;
    const productOptions = this.state.products.map((p, i) => {
      return (<Option key={i} value={p.id}>{ p.name }</Option>);
    });

    return [
      (<FormItem {...formItemLayout} label="Contact First Name" key={1}>
        {getFieldDecorator('first_name',
         { initialValue: this.getInitialValue('first_name'),
           rules: [{ required: true, message: 'Please enter first name', }]})(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Contact Last Name" key={2}>
        {getFieldDecorator('last_name', {
          initialValue: this.getInitialValue('last_name'),
          rules: [{ required: true, message: 'Please enter last name', }]})(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Address" help="Try typing the name of the business" key={3}>
        {getFieldDecorator('address', {
          rules: [{ required: true, message: 'Please choose an address' }]})(
            <MapboxSearchInput onSelect={this.onAddressSelect} initialValue={this.getInitialValue('address')} />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Business Name" key={4}>
        {getFieldDecorator('businessName', {
          initialValue: this.getInitialValue('businessName'),
          rules: [{ required: true, message: 'Please input your username!' }]})(
            <Input name="businessName" />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Phone Number" key={5}>
        {getFieldDecorator('phoneNumber', {
          initialValue: this.getInitialValue('phoneNumber'),
          rules: [{ required: true, message: 'Please input a phone number!' }],})(
            <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Cell Phone Number" key={6}>
        {getFieldDecorator('cellPhoneNumber', {
          initialValue: this.getInitialValue('cellPhoneNumber'),
          rules: [{ required: true, message: 'Please input a cell phone number!' }]})(
          <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
    ];
  }

}

export default CustomerForm;
