import React, { Component } from 'react';
import { Form, Input, Select, Upload, Icon, Button } from 'antd';
import { getProducts, getSafetyWears } from '../../util/DjangoApi';
import { tailFormItemLayout, formItemLayout } from '../../constants/tableLayout';
import Cloudinary from '../../util/Cloudinary';
import base64File from '../../util/Base64File';

const uploader = new Cloudinary();
const { TextArea } = Input;
const FormItem = Form.Item;
const Option = Select.Option;

class ProductForm extends Component {

  state = {
    imageFiles: [],
    products: [],
    safetyWears: [],
    safetyWearOptions: [],
  }

  getInitialValue = (key) => {
    if(!this.props.recordToEdit) {
      return;
    }
    return this.props.recordToEdit[key]
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

  prepareValues = async (values) => {

    const { imageFiles } = this.state;

    const primaryImage = await uploader.upload(imageFiles[0]);
    const secondaryImage = await uploader.upload(imageFiles[1]);

    const sdsSheetB64 = await base64File(values.sdsSheet.file.originFileObj);
    const infoSheetB64 = await base64File(values.infoSheet.file.originFileObj);

    const newProduct = Object.assign({}, values, {
      primaryImageLink: primaryImage.url,
      secondaryImageLink: secondaryImage.url,
      sdsSheet: sdsSheetB64,
      infoSheet: infoSheetB64,
    });

    return newProduct;
  }

  onCreateProduct(response) {
    this.props.onNewRecord(response);
  }

  onBeforeImageUpload = (imgFile) => {
    if(imgFile) {
      this.setState({
        imageFiles: [...this.state.imageFiles, imgFile],
      });
    }
  }

  onImageRemove = (img) => {
    const imageFiles = this.state.imageFiles.filter(
      f => f.uid !== img.originFileObj.uid);
    debugger;
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

  render() {
    const { getFieldDecorator } = this.props.form;
    const req = true;
    const uploadsRequired = !this.props.recordToEdit;
    console.log(this.props.recordToEdit)
    return (
      <Form onSubmit={this.handleSubmit} ref="form">
        <FormItem {...formItemLayout} label="Name">
          {getFieldDecorator('name', { initialValue: this.getInitialValue('name'),
            rules: [{ required: req, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Brand">
          {getFieldDecorator('brand', { initialValue: this.getInitialValue('brand'),
          rules: [{required: req, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Product Code">
          {getFieldDecorator('productCode', { initialValue: this.getInitialValue('productCode'),
          rules: [{required: req, message: 'Required!'}]})(
            <Input />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Usage Desc">
          {getFieldDecorator('usageType', { initialValue: this.getInitialValue('usageType'),
          rules: [{required: req, message: 'Required!'}]})(
            <Input placeholder="ie: Hard surface cleaner" />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Amount Desc">
          {getFieldDecorator('amountDesc', { initialValue: this.getInitialValue('amountDesc'),
          rules: [{required: req, message: 'Required!'}]})(
            <TextArea placeholder="ie: Use as required"  />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Instructions">
          {getFieldDecorator('instructions', { initialValue: this.getInitialValue('instructions'),
          rules: [{required: req, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Safety Wear">
          {getFieldDecorator('safetyWears', { initialValue: this.getInitialValue('safetyWears'),
            rules: [{required: req, message: 'Required!'}]})(
            <Select
             mode="multiple"
             style={{ width: '100%' }}
             placeholder="Please select"
             onChange={() => {}}
           >
             { this.state.safetyWearOptions }
           </Select>)}
         </FormItem>

         <FormItem {...formItemLayout} label="SDSSheet .pdf">
           <div className="dropbox">
             {getFieldDecorator('sdsSheet', { valuePropName: 'sDSSheet',
               getValueFromEvent: this.normFile, rules: [{required: uploadsRequired, message: 'Required!'}]
             })(
               <Upload name="files" accept={'.pdf'} multiple={false}>
                 <Button><Icon type="upload" />upload</Button>
               </Upload>
             )}
           </div>
        </FormItem>
        <FormItem {...formItemLayout} label="InfoSheet .pdf">
            <div className="dropbox">
              {getFieldDecorator('infoSheet', { valuePropName: 'infoSheet',
                getValueFromEvent: this.normFile, rules: [{required: uploadsRequired, message: 'Required!'}]
              })(
                <Upload name="files" accept={'.pdf'} multiple={false}>
                  <Button><Icon type="upload" />upload</Button>
                </Upload>
              )}
            </div>
        </FormItem>
        <FormItem {...formItemLayout} extra="Upload Two Photos primary then Secondary" label="Images .png .jpg">
            <div className="dropbox">
              {getFieldDecorator('images', { valuePropName: 'Images',
                getValueFromEvent: this.normFile, rules: [{required: uploadsRequired, message: '2 Images Required!'}],
              })(<div>{ this.renderImageUpload() }</div>)}
            </div>
        </FormItem>
        <FormItem { ...tailFormItemLayout }>
          <Button type="primary" htmlType="submit"
            disabled={ uploadsRequired && this.state.imageFiles.length < 2 }
            onClick={this.handleSubmit}>
            Done
          </Button>
        </FormItem>
      </Form>
    );
  }


}

export default ProductForm;
