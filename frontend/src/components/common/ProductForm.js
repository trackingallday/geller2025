import React, { Component } from 'react';
import { Form, Input, Select } from 'antd';
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

class ProductForm extends Component {

  state = {
    files: [],
  }

  getInitialValue(key) {
    if(!this.props.productToEdit) {
      return;
    }
    return this.props.productToEdit[key]
  }

  componentDidMount() {
    getProducts( (products) => {
      this.setState({ products });
    });
  }

  handleSubmit = (e) => {
    e.preventDefault();
    this.props.form.validateFieldsAndScroll((err, values) => {
      if (!err) {
        const data = Object.assign(values, { geocodingDetail: this.state.addressResult });
        postNewCustomer(data, (response) => {
          this.props.onCreate(response);
        });
      }
    });
  }
  'id', 'name', 'primaryImageLink', 'secondaryImageLink', 'usageType', 'amountDesc',
            'instructions', 'productCode', 'brand', 'infoSheet', 'sdsSheet',
            'safetyWears', 'customers',

  render() {
    const { getFieldDecorator } = this.props.form;
    return (
      <Form onSubmit={this.handleSubmit} ref="form">
        <FormItem
          {...formItemLayout}
          label="Name"
        >
          {getFieldDecorator('name', {
            rules: [
              { required: true, message: 'Please input an name!'},
            ],
          })(<Input />)}
        </FormItem>
        <FormItem {...formItemLayout}
          label="Password"
          help="Please set a temporary password for the customer"
        >
          {getFieldDecorator('password', {
            rules: [{
              required: true, message: 'Please input your password!',
            }, {
              validator: this.checkConfirm,
            }],
          })(
            <Input type="password" />
          )}
        </FormItem>
        <FormItem
          {...formItemLayout}
          label="Confirm Password"
        >
          {getFieldDecorator('confirm', {
            rules: [{
              required: true, message: 'Please confirm your password!',
            }, {
              validator: this.checkPassword,
            }],
          })(
            <Input type="password" onBlur={this.handleConfirmBlur} />
          )}
        </FormItem>
          { this.renderCommonFormFields() }
        <FormItem {...tailFormItemLayout}>
          <Button type="primary" htmlType="submit" onClick={this.handleSubmit}>Register</Button>
        </FormItem>
      </Form>
    );
  }


}

export default ProductForm;
