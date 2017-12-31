import React, { Component } from 'react';
import { Modal, Button, notification, Row, Col, Form  } from 'antd';

const openNotification = ({ message, description }) => {
  const args = {
    message,
    description,
    duration: 6,
  };
  notification.open(args);
};


export default class RecordAdmin extends Component {

  constructor() {
    super();
    this.state = {
      filterDropdownVisible: false,
      recordsData: [],
      searchText: '',
      filtered: false,
      recordToEdit: null,
      showNew: null,
      showEdit: null,
    };
  }

  componentDidMount() {
    console.log(this.props)
  }

  toggleNew = () => {
    if(!this.state.showNew) {
      this.MyNewRecordForm = Form.create()(this.props.newForm);
    }
    this.setState({
      showNew: this.state.showNew ? null : true,
    });
  }

  toggleEdit = (value, record) => {
    if(!this.state.showEdit) {
      this.MyEditRecordForm = Form.create(record)(this.props.editForm);
    }
    this.setState({
      showEdit: this.state.showEdit ? null : true,
      recordToEdit: record,
    });
  }

  onNewRecord = (response) => {
    this.props.stopLoading();
    this.toggleNew();
    this.props.getDataFunc();
    openNotification({ message: response.data.message,
      description: `Nice work you have successfully added a ${this.props.recordType}`});
  }

  onEditRecord = (response) => {
    this.props.stopLoading();
    this.toggleEdit();
    this.props.getDataFunc();
    openNotification({ message: response.data.message,
      description: `Wonderful work you have successfully edited the ${this.props.recordType}`});
  }

  render = () => {

    const { state, toggleNew, toggleEdit, onNewRecord, onEditRecord } = this;
    const { showNew, showEdit, recordToEdit } = state;
    const { customers, products, safetyWears, distributors, records } = this.props;

    const newFormProps = {
      onNewRecord,
      recordsData: records,
      startLoading: this.props.startLoading,
      customers,
      products,
      safetyWears,
      distributors,
    };

    const editFormProps = {
      onEditRecord,
      recordToEdit,
      recordsData: records,
      startLoading: this.props.startLoading,
      customers,
      products,
      safetyWears,
      distributors,
    }

    const MyNewRecordForm = this.MyNewRecordForm;
    const MyEditRecordForm = this.MyEditRecordForm;
    const RecordsTable = this.props.recordsTable;

    return (
      <div>
        <Row type="flex" justify="end" style={{ paddingBottom: 12}}>
          <Col span={21}>
          </Col>
          <Col span={3}>
            <Button onClick={toggleNew}>New {this.props.recordType}</Button>
          </Col>
        </Row>
        <Row>
          <Col span={24}>
            <RecordsTable data={records} onEditClick={this.toggleEdit} />
          </Col>
        </Row>
        <Modal
          title={`Create new ${this.props.recordType}`}
          visible={showNew}
          footer={null}
          onCancel={toggleNew}
        >
          { showNew && <MyNewRecordForm { ...newFormProps }/> }
        </Modal>
        <Modal
          title={`Edit ${this.props.recordType}`}
          visible={showEdit}
          footer={null}
          onCancel={toggleEdit}
        >
          { showEdit && <MyEditRecordForm { ...editFormProps } /> }
        </Modal>
      </div>
    );
  }

}
