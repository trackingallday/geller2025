import React from 'react';
import { Form, Button } from 'antd';
import { postNewCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';
import { tailFormItemLayout } from '../../constants/tableLayout';


const FormItem = Form.Item;

class NewCustomerForm extends CustomerForm {

  handleSubmit = (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFieldsAndScroll((err, values) => {
      this.setState({ submitting: true })
      if (!err) {
        this.props.startLoading();
        const data = Object.assign(values, { geocodingDetail: this.state.addressResult });
        postNewCustomer(data, (response) => {
          this.props.onNewRecord(response);
        });
      } else {
        this.setState({ submitting: false })
      }
    });
  }

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit} ref="form">
        { this.renderCommonFormFields() }
        <FormItem {...tailFormItemLayout}>
          <Button type="primary" htmlType="submit" onClick={this.handleSubmit}>Register</Button>
        </FormItem>
      </Form>
    );
  }
}

export default NewCustomerForm;
