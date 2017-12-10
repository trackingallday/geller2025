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
      recordssData: [],
      searchText: '',
      filtered: false,
      recordToEdit: null,
      showNew: null,
      showEdit: null,
    };
  }

  componentDidMount() {
    this.getRecordsData();
  }

  getRecordsData = () => {
    this.props.getDataFunc((records) => {
      this.setState({
        recordsData: records,
      });
    });
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
      console.log(value, record)
      this.MyEditRecordForm = Form.create(record)(this.props.editForm);
    }
    this.setState({
      showEdit: this.state.showEdit ? null : true,
      recordToEdit: record,
    });
  }

  onNewRecord = (response) => {
    this.toggleNew();
    this.getRecordsData();
    openNotification({ message: response.data.message,
      description: `Nice work you have successfully added a ${this.props.recordType}`});
  }

  onEditRecord = (response) => {
    this.toggleEdit();
    this.getRecordsData();
    openNotification({ message: response.data.message,
      description: `Wonderful work you have successfully edited the ${this.props.recordType}`});
  }

  render = () => {

    const { state, toggleNew, toggleEdit, onNewRecord, onEditRecord } = this;
    const { showNew, showEdit, recordsData, recordToEdit } = state;

    const formProps = {
      onNewRecord,
      onEditRecord,
      recordsData,
      recordToEdit,
    };
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
            <RecordsTable data={state.recordsData} onEditClick={this.toggleEdit} />
          </Col>
        </Row>
        <Modal
          title={`Create new ${this.props.recordType}`}
          visible={showNew}
          footer={null}
          onCancel={toggleNew}
        >
          { showNew && <MyNewRecordForm { ...formProps }/> }
        </Modal>
        <Modal
          title={`Edit ${this.props.recordType}`}
          visible={showEdit}
          footer={null}
          onCancel={toggleEdit}
        >
          { showEdit && <MyEditRecordForm { ...formProps } /> }
        </Modal>
      </div>
    );
  }

}
