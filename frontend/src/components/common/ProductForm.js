import React, { Component } from 'react';
import { Form, Input, Select, Upload, Button } from 'antd';
import { getProducts, getSafetyWears } from '../../util/DjangoApi';
import { tailFormItemLayout } from '../../constants/tableLayout';


const { TextArea } = Input;
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

class ProductForm extends Component {

  state = {
    files: [],
    products: [],
    safetyWears: [],
    safetyWearOptions: [],
  }

  getInitialValue(key) {
    if(!this.props.productToEdit) {
      return;
    }
    return this.props.productToEdit[key]
  }

  componentDidMount() {
    getProducts((products) => {
      this.setState({ products });
    });

    getSafetyWears((safetyWears) => {
      this.setState({
        safetyWears,
        safetyWearOptions: safetyWears.map((sw, i) => (
          <Option key={i} value={sw.id}>{ sw.name }</Option>
        )),
      });
    });

  }

  render() {
    const { getFieldDecorator } = this.props.form;
    return (
      <Form onSubmit={this.handleSubmit} ref="form">
        <FormItem {...formItemLayout} label="Name">
          {getFieldDecorator('name', {rules: [{ required: true, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Brand">
          {getFieldDecorator('brand', { rules: [{required: true, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Product Code">
          {getFieldDecorator('productCode', { rules: [{required: true, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Usage Desc"
          placeholder="ie: Hard surface cleaner"
          help="Please set a temporary password for the customer">
          {getFieldDecorator('usageType', { rules: [{required: true, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Amount Desc">
          {getFieldDecorator('amountDesc', { rules: [{required: true, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Instructions">
          {getFieldDecorator('instructions', { rules: [{required: true, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Safety Wear">
          {getFieldDecorator('safetyWears', { rules: [{required: true, message: 'Required!'}]})(
            <Select
             mode="multiple"
             style={{ width: '100%' }}
             placeholder="Please select"
             onChange={() => {}}
           >
             { this.state.safetyWearOptions }
           </Select>)}
        </FormItem>
        <FormItem { ...tailFormItemLayout }>
          <Button type="primary" htmlType="submit" onClick={this.handleSubmit}>Done</Button>
        </FormItem>
      </Form>
    );
  }


}

export default ProductForm;
