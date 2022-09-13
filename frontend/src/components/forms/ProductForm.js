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

async function readFiles(file) {
  return new Promise(resolve => {
    var FR= new FileReader();
    FR.addEventListener("load", function(e) {
      resolve(e.target.result);
    });
    FR.readAsDataURL(file);
  });
}

class ProductForm extends Component {

  state = {
    imageFiles: [],
    products: [],
    safetyWearOptions: [],
    markets: [],
    marketOptions: [],
    categoryOptions: [],
    sizeOptions: [],
    subCategoryOptions: [],
  }

  getInitialValue = (key) => {
    if(!this.props.recordToEdit) {
      return;
    }
    return this.props.recordToEdit[key]
  }

  componentDidMount() {
    const { products, safetyWears, markets, categories, sizes } = this.props;
    this.setState({
      safetyWears,
      products,
      safetyWearOptions: safetyWears.map((sw, i) => (
        <Option key={i+"a"} value={sw.id}>{ sw.name }</Option>
      )),
      markets,
      marketOptions: markets.map((sw, i) => (
        <Option key={i+"b"} value={sw.id}>{ sw.name }</Option>
      )),
      categoryOptions: categories.filter(cs => !cs.isSubCategory).map((sw, i) => (
        <Option key={i+"b"} value={sw.id}>{ sw.name }</Option>
      )),
      subCategoryOptions: categories.filter(cs => !!cs.isSubCategory).map((sw, i) => (
        <Option key={i+"34"} value={sw.id}>{ sw.name }</Option>
      )),
      sizeOptions: sizes.map((sw, i) => (
        <Option key={i+"b"} value={sw.id}>{ sw.name }</Option>
      )),
    });
  }

  prepareValues = async (values) => {

    const { imageFiles } = this.state;
    let primaryImageLink = null;
    let secondaryImageLink = null;
    let infoSheet = null;
    let sdsSheet = null;

    if(imageFiles[0]) primaryImageLink = await readFiles(imageFiles[0]);
    if(imageFiles[1]) secondaryImageLink = await readFiles(imageFiles[1]);

    let newProduct = Object.assign({}, values, {
      primaryImageLink: primaryImageLink,
      secondaryImageLink: secondaryImageLink
    });

    if(values.sdsSheet && values.sdsSheet.originFileObj) {
      sdsSheet = await base64File(values.sdsSheet.originFileObj);
      newProduct.sdsSheet = sdsSheet;
    }

    if(values.infoSheet && values.infoSheet.originFileObj) {
      infoSheet = await base64File(values.infoSheet.originFileObj);
      newProduct.infoSheet = infoSheet;
    }

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

  normFile = (e) => {
    return e.file;
  }

  render() {
    if(!this.props.recordToEdit) {
      return <div />
    }
    const { getFieldDecorator } = this.props.form;
    const { recordToEdit } = this.props;
    const req = true;
    const uploadsRequired = !recordToEdit;

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
        <FormItem {...formItemLayout} label="Directions">
          {getFieldDecorator('directions', { initialValue: this.getInitialValue('directions'),
          rules: [{required: req, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Applications">
          {getFieldDecorator('application', { initialValue: this.getInitialValue('application'),
          rules: [{required: req, message: 'Required!'}]})(
            <TextArea placeholder="ie: Use for Carpets, and mats"  />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Properties">
          {getFieldDecorator('properties', { initialValue: this.getInitialValue('properties'),
          rules: [{required: req, message: 'Required!'}]})(
            <TextArea />)}
        </FormItem>
        <FormItem {...formItemLayout} label="Description">
          {getFieldDecorator('description', { initialValue: this.getInitialValue('description'),
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
         <FormItem {...formItemLayout} label="Markets">
           {getFieldDecorator('markets', { initialValue: this.getInitialValue('markets'),
             rules: [{required: req, message: 'Required!'}]})(
             <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="Please select"
              onChange={() => {}}
            >
              { this.state.marketOptions }
            </Select>)}
          </FormItem>
          <FormItem {...formItemLayout} label="Category">
            {getFieldDecorator('productCategory', { initialValue: this.getInitialValue('productCategory'),
              rules: [{required: req, message: 'Required!'}]})(
              <Select
               style={{ width: '100%' }}
               mode="multiple"
               placeholder="Please select"
               onChange={() => {}}
             >
               { this.state.categoryOptions }
             </Select>)}
           </FormItem>
           <FormItem {...formItemLayout} label="Sub Category">
             {getFieldDecorator('subCategory', { initialValue: this.getInitialValue('subCategory'),
             rules: [{required: req, message: 'Required!'}]})(
                 <Select
                  style={{ width: '100%' }}
                  mode="multiple"
                  placeholder="Please select"
                  onChange={() => {}}
                >
                  { this.state.subCategoryOptions }
                </Select>)}
           </FormItem>
           <FormItem {...formItemLayout} label="Sizes">
             {getFieldDecorator('sizes', { initialValue: this.getInitialValue('sizes'),
               rules: [{required: req, message: 'Required!'}]})(
               <Select
                style={{ width: '100%' }}
                mode="multiple"
                placeholder="Please select"
                onChange={() => {}}
              >
                { this.state.sizeOptions }
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
        <FormItem {...formItemLayout} extra="Upload a Product Image then an Application Image" label="Images .png .jpg">
            <div className="dropbox">
              {getFieldDecorator('images', {
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
