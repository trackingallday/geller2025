import React from 'react';
import { Form, Button } from 'antd';
import { postNewCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';
import { tailFormItemLayout } from '../../constants/tableLayout';
import { openNotification } from './../common/RecordAdmin'

const FormItem = Form.Item;

class NewCustomerForm extends CustomerForm {

  handleSubmit = (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFieldsAndScroll((err, values) => {
      if (!err) {
        this.setState({ submitting: true })
        this.props.startLoading();
        const data = Object.assign(values, { geocodingDetail: this.state.addressResult });
        postNewCustomer(data, (response) => {
          this.props.onNewRecord(response);
        }, (err) => {
          openNotification({ message: 'There was a problem adding the record',
            description: err.response.data.error});
          this.setState({ submitting: false })
          this.props.stopLoading();
        });
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
