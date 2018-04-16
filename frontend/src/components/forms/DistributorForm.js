import React, { Component } from 'react';
import { Form, Input, Select, Upload, Icon, Button } from 'antd';
import MapboxSearchInput from '../common/MapboxSearchInput';
import CustomerForm from './CustomerForm';
import { tailFormItemLayout, formItemLayout } from '../../constants/tableLayout';
import Cloudinary from '../../util/Cloudinary';
import base64File from '../../util/Base64File';


const FormItem = Form.Item;
const Option = Select.Option;
const uploader = new Cloudinary();

async function readFile(file) {
  return new Promise(resolve => {
    var FR= new FileReader();
    FR.addEventListener("load", function(e) {
      resolve(e.target.result);
    });
    FR.readAsDataURL(file);
  });
}

class DistributorForm extends CustomerForm {

  state = {
    confirmPasswordValue: false,
    autoCompleteResult: [],
    addressResult: null,
    imageFiles: [],
  };

  onBeforeImageUpload = (imgFile) => {
    if(imgFile) {
      this.setState({
        imageFiles: [imgFile],
      });
    }
  }

  prepareValues = async (values) => {

    const { imageFiles } = this.state;

    if(imageFiles[0]) {
      const base64Img = await readFile(imageFiles[0]);
      let newDistributor = Object.assign({}, values, {
        primaryImageLink: base64Img,
      });
      return newDistributor;
    }
    return values;
  }

  normFile = (e) => {
    return [ ...e.target.files ]
  }

  onImageRemove = (img) => {
    const imageFiles = this.state.imageFiles.filter(
      f => f.uid !== img.originFileObj.uid);

    this.setState({ imageFiles });
  }

  renderImageUpload = () => {
    const imageUploaderProps = {
      beforeUpload: this.onBeforeImageUpload,
      onRemove: this.onImageRemove,
      listType: 'picture',
      defaultFileList: [],
      className: 'upload-list-inline',
    };
    return (
      <Upload { ...imageUploaderProps } disabled={this.state.imageFiles.length > 1}>
        <Button><Icon type="upload" />upload</Button>
      </Upload>
    );
  }

  componentDidMount() {
  }

  renderCommonFormFields() {
    const { getFieldDecorator } = this.props.form;
    const uploadsRequired = false;

    return [
      (<FormItem {...formItemLayout} label="Contact First Name" key={1}>
        {getFieldDecorator('first_name',
         { initialValue: this.getInitialValue('first_name'),
           rules: [{ required: true, message: 'Please enter first name', }]})(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Contact Last Name" key={2}>
        {getFieldDecorator('last_name', {
          initialValue: this.getInitialValue('last_name'),
          rules: [{ required: true, message: 'Please enter last name', }]})(<Input />)}
      </FormItem>),
      (<FormItem
        {...formItemLayout}
        label="Email"
       >
        {getFieldDecorator('email', {
          initialValue: this.getInitialValue('email'),
          rules: [
            { required: true, message: 'Please input an email!'},
            { validator: this.checkEmail},
          ],
        })(<Input />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Address" help="Try typing the name of the business" key={3}>
        {getFieldDecorator('address', {
          initialValue: this.getInitialValue('address'),
          rules: [{ required: true, message: 'Please choose an address' }]})(
            <MapboxSearchInput onSelect={this.onAddressSelect} initialValue={this.getInitialValue('address')} />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Business Name" key={4}>
        {getFieldDecorator('businessName', {
          initialValue: this.getInitialValue('businessName'),
          rules: [{ required: true, message: 'Please input your username!' }]})(
            <Input name="businessName" />)}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Phone Number" key={5}>
        {getFieldDecorator('phoneNumber', {
          initialValue: this.getInitialValue('phoneNumber'),
          rules: [{ required: true, message: 'Please input a phone number!' }],})(
            <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
      (<FormItem {...formItemLayout} label="Cell Phone Number" key={6}>
        {getFieldDecorator('cellPhoneNumber', {
          initialValue: this.getInitialValue('cellPhoneNumber'),
          rules: [{ required: true, message: 'Please input a cell phone number!' }]})(
          <Input style={{ width: '100%' }} />
        )}
      </FormItem>),
      (<FormItem key={7} {...formItemLayout} extra="Upload Distributor Logo" label="Images .png .jpg">
          <div className="dropbox">
            {getFieldDecorator('primaryImageLink', {
              getValueFromEvent: this.normFile, rules: [],
            })(<div>{ this.renderImageUpload() }</div>)}
          </div>
      </FormItem>),
      (<FormItem key={8}{ ...tailFormItemLayout }>
        <Button type="primary" htmlType="submit"
          disabled={ uploadsRequired && this.state.imageFiles.length < 1 }
          onClick={this.handleSubmit}>
          Done
        </Button>
      </FormItem>),
    ];
  }

}

export default DistributorForm;
