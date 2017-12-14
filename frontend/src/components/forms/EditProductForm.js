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

    if(values.sdsSheet && values.sdsSheet.file.originFileObj) {
      sdsSheet = await base64File(values.sdsSheet.file.originFileObj);
      newProduct.sdsSheet = sdsSheet;
    }

    if(values.infoSheet && values.infoSheet.file.originFileObj) {
      infoSheet = await base64File(values.infoSheet.file.originFileObj);
      newProduct.infoSheet = infoSheet;
    }

    return newProduct;
  }

  handleSubmit = async (e) => {
    e.preventDefault();
    this.props.form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        const newProduct = await this.prepareValues(values);
        postEditProduct(newProduct, this.props.onEditRecord);
      } else {
        console.log(err)
      }
    });
  }

}

export default EditProductForm;
