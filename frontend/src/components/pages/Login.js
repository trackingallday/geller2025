import React, { Component } from 'react';
import BasePage from './BasePage';
import styles from '../../styles';
import { message, Form, Icon, Input, Button, Row, Col, Card } from 'antd';
import { postLogin } from '../../util/DjangoApi';
import { formItemLayout, tailFormItemLayout } from '../../constants/tableLayout';


const FormItem = Form.Item;

class LoginForm extends Component {

  handleSubmit = (e) => {
    e.preventDefault();
    this.props.form.validateFields((err, values) => {
      if (!err) {
        this.props.handleSubmit(values);
      }
    });
  }

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit} className="login-form">
        <Row>
          <Col>
            <FormItem { ...formItemLayout }>
              {getFieldDecorator('username', {
                rules: [{ required: true, message: 'input your username!' }],
              })(
                <Input prefix={<Icon type="user" style={{ color: 'rgba(0,0,0,.25)' }} />} placeholder="Username" />
              )}
            </FormItem>
            <FormItem { ...formItemLayout }>
              {getFieldDecorator('password', {
                rules: [{ required: true, message: 'input your Password!' }],
              })(
                <Input prefix={<Icon type="lock" style={{ color: 'rgba(0,0,0,.25)' }} />} type="password" placeholder="Password" />
              )}
            </FormItem>
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col>
            <FormItem { ...tailFormItemLayout }>
              <Button type="primary" htmlType="submit" className="login-form-button">
                Log in
              </Button>
            </FormItem>
          </Col>
        </Row>
      </Form>
    );
  }

}

const MyLoginForm = Form.create()(LoginForm);


class Login extends BasePage {

  onSuccess = (userDetails) => {
    this.stopLoading();
    this.onLogin(userDetails);
    message.success('Welcome back', 1);
  }

  onFail = (error) => {
    message.error('Please check your details ', 2);
    this.stopLoading();
  }

  handleSubmit = ({ username, password }) => {
    this.startLoading();
    postLogin(username, password, this.onSuccess, this.onFail);
  }

  renderContent() {
    return (
      <div style={styles.container}>
        <div style={{paddingTop: 200, paddingBottom: 200  }}>
            <Row type="flex" justify="end">
              <Col span={6}></Col>
              <Col span={12}>
                <Card title="Please Sign In">
                  <MyLoginForm handleSubmit={this.handleSubmit} />
                </Card>
              </Col>
              <Col span={6}></Col>
            </Row>
        </div>
      </div>
    );
  }

}

export default Login
