import React from 'react';
import { Form, Input, Button } from 'antd';
import { postNewCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';


const FormItem = Form.Item;


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

class NewCustomerForm extends CustomerForm {

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

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit} ref="form">
        <FormItem
          {...formItemLayout}
          label="Email"
        >
          {getFieldDecorator('email', {
            rules: [
              { required: true, message: 'Please input an email!'},
              { validator: this.checkEmail},
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

export default NewCustomerForm;
