import React, { Component } from 'react';
import { Modal, Button, notification, Row, Col, Form  } from 'antd';
import CustomersTable from './CustomersTable';
import NewCustomerForm from '../common/NewCustomerForm';
import EditCustomerForm from '../common/EditCustomerForm';
import { getCustomers } from '../../util/DjangoApi';


const openNotification = ({ message, description }) => {
  const args = {
    message,
    description,
    duration: 6,
  };
  notification.open(args);
};


export default class DistributorCustomers extends Component {

  constructor() {
    super();
    this.state = {
      filterDropdownVisible: false,
      customersData: [],
      searchText: '',
      filtered: false,
      showNew: null,
      showEdit: null,
    };
  }

  componentDidMount() {
    this.getCustomersData();
    this.NewCustomerForm = Form.create()(NewCustomerForm);
    this.MyEditCustomerForm = Form.create()(EditCustomerForm);
  }

  getCustomersData = () => {
    getCustomers( (customers) => {
      this.setState({
        customersData: customers,
      });
    });
  }

  onMenuClick = ({ item, key, keyPath }) => {
    this.setState({ selectedMenuItem: key })
  }

  toggleNew = () => {
    if(this.state.show) {
      this.props.form.resetFields();
    }
    this.setState({
      showNew: this.state.showNew ? null : true,
    });
  }

  toggleEdit = (value, record) => {
    if(!this.state.showEdit) {
      this.MyEditCustomerForm = Form.create(record)(EditCustomerForm);
    }
    this.setState({
      showEdit: this.state.showEdit ? null : true,
      customerToEdit: record,
    });
  }

  onNewCustomer = (response) => {
    this.toggleNew();
    this.getCustomersData();
    openNotification({ message: response.data.message,
      description: 'Nice work you have successfully added a customer'});
  }

  onEditCustomer = (response) => {
    this.toggleEdit();
    this.getCustomersData();
    openNotification({ message: response.data.message,
      description: 'Wonderful work you have successfully edited the customer'});
  }

  render = () => {

    const { state, toggleNew, toggleEdit, onNewCustomer, onEditComplete } = this;
    const { showNew, showEdit, customersData, customerToEdit } = state;

    const formProps = {
      onCreate: onNewCustomer,
      onEditComplete: this.onNewCustomer,
      customersData,
      customerToEdit,
    };

    const MyNewCustomerForm = this.MyNewCustomerForm;
    const MyEditCustomerForm = this.MyEditCustomerForm;

    return (
      <div>
        <Row type="flex" justify="end" style={{ paddingBottom: 12}}>
          <Col span={21}>
          </Col>
          <Col span={3}>
            <Button onClick={toggleNew}>New Customer</Button>
          </Col>
        </Row>
        <Row>
          <Col span={24}>
            <CustomersTable data={state.customersData} onEditClick={this.toggleEdit} />
          </Col>
        </Row>
        <Modal
          title="Create new customer"
          visible={showNew}
          footer={null}
          onCancel={toggleNew}
        >
          { showNew && <MyNewCustomerForm { ...formProps }/> }
        </Modal>
        <Modal
          title="Edit customer"
          visible={showEdit}
          footer={null}
          onCancel={toggleEdit}
        >
          { showEdit && <MyEditCustomerForm { ...formProps } /> }
        </Modal>
      </div>
    );
  }

}
