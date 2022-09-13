import React from 'react';
import { Form, Button } from 'antd';
import { postEditCustomer } from '../../util/DjangoApi';
import CustomerForm from './CustomerForm';
import { tailFormItemLayout } from '../../constants/tableLayout';
import { openNotification } from './../common/RecordAdmin'

const FormItem = Form.Item;

class EditCustomerForm extends CustomerForm {

  handleSubmit = (e) => {
    e.preventDefault();
    const { form, recordToEdit, onEditRecord } = this.props;

    form.validateFieldsAndScroll((err, values) => {
      if (!err) {
        this.setState({ submitting: true })
        this.props.startLoading();
        const data = Object.assign(values, { id: recordToEdit.id });
        if(this.state.addressResult !== "initialValue") {
          data.geocodingDetail = this.state.addressResult;
        }
        postEditCustomer(data, (response) => {
          onEditRecord(response);
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
