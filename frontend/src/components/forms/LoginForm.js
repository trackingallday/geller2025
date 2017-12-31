import React, { Component } from 'react';
import { message, Form, Icon, Input, Button, Row, Col, Card } from 'antd';
import { postLogin } from '../../util/DjangoApi';
import { formItemLayout, tailFormItemLayout } from '../../constants/tableLayout';


const FormItem = Form.Item;


class LoginForm extends Component {

  onLogin = (userDetails) => {
    this.stopLoading();
    message.success('Great Welcome back', 3);
    this.props.onLogin(userDetails);
  }

  onFail = (message) => {
    message.success('Please check your details', 3);
    this.props.stopLoading();
  }

  handleSubmit = (e) => {
    e.preventDefault();
    if(this.state.submitting) {
      return;
    }
    this.props.form.validateFields((err, values) => {
      if (!err) {
        this.setState({ submitting: true })
        this.props.startLoading();
        postLogin(values.username, values.password, this.onLogin)
      } else {
        this.stopLoading();
      }
    });
  }

  render() {
    const { getFieldDecorator } = this.props.form;
    return (
      <div style={{paddingTop: 200, paddingBottom: 200  }}>
          <Row type="flex" justify="end">
            <Col span={6}></Col>
            <Col span={12}>
              <Card title="Please Sign In">
                <Form onSubmit={this.handleSubmit} className="login-form">
                  <Row>
                    <Col>
                      <FormItem { ...formItemLayout }>
                        {getFieldDecorator('userName', {
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
              </Card>
            </Col>
            <Col span={6}></Col>
          </Row>
      </div>
    );
  }
}

const WrappedLoginForm = Form.create()(LoginForm);

export default WrappedLoginForm
