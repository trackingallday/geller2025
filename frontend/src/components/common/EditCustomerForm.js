import React, { Component } from 'react';
import { Form, Input, Tooltip, Icon, Cascader, Select, Row, Col, Checkbox, Button, AutoComplete } from 'antd';
import MapboxSearchInput from './MapboxSearchInput';
import { getProducts, postNewCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';

const FormItem = Form.Item;
const Option = Select.Option;
const AutoCompleteOption = AutoComplete.Option;



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
const tailFormItemLayout = {
  wrapperCol: {
    xs: {
      span: 24,
      offset: 0,
    },
    sm: {
      span: 16,
      offset: 8,
    },
  },
};

class EditCustomerForm extends CustomerForm {

  handleSubmit = (e) => {
    e.preventDefault();
    this.props.form.validateFieldsAndScroll((err, values) => {
      if (!err) {
        const data = Object.assign(values, { geocodingDetail: this.state.addressResult });
        /*postNewCustomer(data, (response) => {
          this.props.onCreate(response);
        });*/
      }
    });
  }

  render() {
    const { getFieldDecorator } = this.props.form;
    const { autoCompleteResult } = this.state;

    const websiteOptions = autoCompleteResult.map(website => (
      <AutoCompleteOption key={website}>{website}</AutoCompleteOption>
    ));

    const productOptions = this.state.products.map((p, i) => {
      return (<Option key={i} value={p.id}>{ p.name }</Option>);
    });

    return (
      <Form onSubmit={this.handleSubmit}>
        { this.renderCommonFormFields() }
        <FormItem {...tailFormItemLayout}>
          <Button type="primary" htmlType="submit">Register</Button>
        </FormItem>
      </Form>
    );
  }
}

export default EditCustomerForm;
