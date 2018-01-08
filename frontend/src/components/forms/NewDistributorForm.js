import React from 'react';
import { Form, Input, Button } from 'antd';
import { postNewDistributor } from '../../util/DjangoApi';
import DistributorForm from './DistributorForm';
import { tailFormItemLayout, formItemLayout } from '../../constants/tableLayout';


const FormItem = Form.Item;

class NewDistributorForm extends DistributorForm {

  handleSubmit = async (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        this.setState({ submitting: true })
        this.props.startLoading();
        const newDistributor = await this.prepareValues(values);
        postNewDistributor(newDistributor, this.props.onNewRecord);
      }
    });
  }

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit} ref="form">
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
      </Form>
    );
  }
}

export default NewDistributorForm;
