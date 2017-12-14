import React from 'react';
import { Form, Button } from 'antd';
import { postEditCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';
import { tailFormItemLayout } from '../../constants/tableLayout';

const FormItem = Form.Item;

class EditCustomerForm extends CustomerForm {

  handleSubmit = (e) => {
    e.preventDefault();
    const { form, recordToEdit, onEditRecord } = this.props;

    form.validateFieldsAndScroll((err, values) => {
      if (!err) {
        const data = Object.assign(values, { id: recordToEdit.id });
        if(this.state.addressResult !== "initialValue") {
          data.geocodingDetail = this.state.addressResult;
        }
        postEditCustomer(data, (response) => {
          onEditRecord(response);
        });
      }
    });
  }

  render() {
    return (
      <Form onSubmit={this.handleSubmit}>
        { this.renderCommonFormFields() }
        <FormItem {...tailFormItemLayout}>
          <Button type="primary" htmlType="submit">Done</Button>
        </FormItem>
      </Form>
    );
  }
}

export default EditCustomerForm;
