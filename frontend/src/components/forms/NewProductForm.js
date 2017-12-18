import { postNewProduct } from '../../util/DjangoApi';
import ProductForm from './ProductForm';


class NewProductForm extends ProductForm {

  handleSubmit = async (e) => {
    e.preventDefault();
    this.props.form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        this.props.startLoading();
        const newProduct = await this.prepareValues(values);
        postNewProduct(newProduct, this.props.onNewRecord);
      }
    });
  }

}

export default NewProductForm;
