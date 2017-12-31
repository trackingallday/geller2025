import { postNewProduct } from '../../util/DjangoApi';
import ProductForm from './ProductForm';


class NewProductForm extends ProductForm {

  handleSubmit = async (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFieldsAndScroll(async (err, values) => {
      if (!err) {
        this.setState({ submitting: true })
        this.props.startLoading();
        const newProduct = await this.prepareValues(values);
        postNewProduct(newProduct, this.props.onNewRecord);
      }
    });
  }

}

export default NewProductForm;
