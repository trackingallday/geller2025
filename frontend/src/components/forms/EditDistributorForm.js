import React from 'react';
import { Form, Button } from 'antd';
import { postEditDistributor } from '../../util/DjangoApi';
import DistributorForm from './DistributorForm';
import { tailFormItemLayout } from '../../constants/tableLayout';

const FormItem = Form.Item;

class EditDistributorForm extends DistributorForm {

  handleSubmit = (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    const { form, recordToEdit, onEditRecord } = this.props;

    form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        this.props.startLoading();
        this.setState({ submitting: true })
        const data = Object.assign(values, { id: recordToEdit.id });
        const newDistributor = await this.prepareValues(data);
        postEditDistributor(newDistributor, (response) => {
          onEditRecord(response);
        });
      }
    });
  }

  render() {
    return (
      <Form onSubmit={this.handleSubmit}>
        { this.renderCommonFormFields() }
      </Form>
    );
  }
}

export default EditDistributorForm;
