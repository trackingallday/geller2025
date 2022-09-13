import { postEditProduct } from '../../util/DjangoApi';
import ProductForm from './ProductForm';
import base64File from '../../util/Base64File';
import Cloudinary from '../../util/Cloudinary';
import { openNotification } from './../common/RecordAdmin'


const uploader = new Cloudinary();


class EditProductForm extends ProductForm {

  prepareValues = async (values) => {

    const { imageFiles } = this.state;
    const { recordToEdit } = this.props;

    let primaryImageLink = recordToEdit.primaryImageLink;
    let secondaryImageLink = recordToEdit.secondaryImageLink;
    let infoSheet = null;
    let sdsSheet = null;

    if(imageFiles.length) {
      const primaryImage = await uploader.upload(imageFiles[0]);
      const secondaryImage = await uploader.upload(imageFiles[1]);
      primaryImageLink = imageFiles[0] && primaryImage;
      secondaryImageLink = imageFiles[1] && secondaryImage;
    }

    let newProduct = Object.assign(recordToEdit, values, {
      primaryImageLink,
      secondaryImageLink,
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

  handleSubmit = async (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        this.setState({ submitting: true });
        this.props.startLoading();
        const newProduct = await this.prepareValues(values);
        postEditProduct(newProduct, this.props.onEditRecord, (err) => {
          openNotification({ message: 'There was a problem adding the record',
            description: err.response.data.error});
          this.setState({ submitting: false })
          this.props.stopLoading();
        });
      }
    });
  }

}

export default EditProductForm;
