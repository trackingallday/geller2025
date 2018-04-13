import { postEditProduct } from '../../util/DjangoApi';
import ProductForm from './ProductForm';
import base64File from '../../util/Base64File';
import Cloudinary from '../../util/Cloudinary';


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
      primaryImageLink = primaryImage.url;
      secondaryImageLink = secondaryImage.url;
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
        postEditProduct(newProduct, this.props.onEditRecord);
      } else {
        console.log(err)
      }
    });
  }

}

export default EditProductForm;
