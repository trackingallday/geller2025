import React, { Component } from 'react';
import { withRouter } from 'react-router';
import superagent from 'superagent';
import { GoogleReCaptcha } from 'react-google-recaptcha-v3';


import URI from '../../constants/serverUrl';
//const URI = 'http://localhost:8000';

class Contact extends Component {

  state = {
    loading: false,
    result: 'unset',
    captcha_token: null,
    refreshReCaptcha: null
  }

  onFormSubmit(e) {
    e.preventDefault();
    this.setState({loading: true})
    let data = new FormData(e.target);
    var params = {};
    data.forEach(function(value, key){
        params[key] = value;
    });
    params["captcha_token"] = this.state.captcha_token
    console.log(params)
    var json = JSON.stringify(params);
    this.setState({refreshReCaptcha: Date.now()})
    superagent.get(URI + '/create_contact/')
      .query({data: json})
      .set('Accept', 'application/json')
      .end((err, res) => {
        if (err) {
          this.setState({loading: false, result: 'failure'})
        } else {
          this.setState({loading: false, result: 'success'})
        }
      });
  }

  handleVerify = (e) => {
    console.log(e)
    this.setState({captcha_token: e})
  }

  render() {
    const { ph_number, email_address, company_name, company_address } = this.props.configs;
    let messageInput = (
      <textarea name="content" id="message" className="form-control" rows="9" cols="25" required="required"
          placeholder="Message"></textarea>
    );
    if(this.props.message) {
      let value = 'Inquiry regarding: ' + this.props.message;
      messageInput =  (
        <textarea name="content" id="message" value={value} onChange={() => {}} className="form-control" rows="9" cols="25" required="required"
            placeholder="Message"></textarea>
      );
    }
    return (
      <div>
        <div className="row">
            <div className="col-md-6">
              <div className="med-right">
                <div className="hexagon white"></div>
              </div>
              <div style={{height: '80px', width: '100%'}}></div>
          </div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '30px', paddingTop: '15px', paddingBottom: '170px'}}>
          <div className="col-md-4">
            <h3>{company_name}</h3>
            <p>{company_address}</p>
            <p>{ph_number}</p>
            <p>{email_address}</p>
          </div>
          <div className="col-md-8">
            <div className="well well-md">

              {!this.state.loading && this.state.result == 'unset' && <form onSubmit={(e) => this.onFormSubmit(e)}>
                <div className="col-md-6">
                  <h3>Drop us a line</h3>
                  <p></p>
                    <div className="form-group">
                        <label>
                            Name</label>
                        <input name="nameFrom" type="text" className="form-control" id="name" placeholder="Enter name" required="required" />
                    </div>
                    <div className="form-group">
                        <label>
                            Email Address</label>
                        <div className="input-group">
                            <span className="input-group-addon"><span className="glyphicon glyphicon-envelope"></span>
                            </span>
                            <input name="emailFrom" type="email" className="form-control" id="email" placeholder="Enter email" required="required" /></div>
                    </div>
                </div>
                <div className="col-md-6">
                    <div className="form-group">
                        <label>
                            Message</label>
                          {messageInput}
                    </div>
                </div>
                <div className="col-md-12">
                    <GoogleReCaptcha onVerify={this.handleVerify} refreshReCaptcha={this.state.refreshReCaptcha} />
                    <button type="submit" className="btn btn-primary pull-right" id="btnContactUs" style={{cursor:'pointer'}}>
                        Send Message</button>
                </div>
              </form>}
              {this.state.loading && <div className="col-md-6">
                <div className="row" style={{paddingTop: '130px'}}>
                  <div className="col-md-2">
                  </div>
                  <div className="col-md-8">
                    <div className="bouncing">
                      <img src={require('../../assets/email.png')} />
                    </div>
                  </div>
                </div>
              </div>}
              {this.state.result == 'success' && <div className="col-md-6">
                <h3>Thank you for the message!</h3>
                <p></p>
                <p>We will be in touch soon.</p>
              </div>}
              {this.state.result == 'failure' && <div className="col-md-6">
                <h3>There was an issue with sending the email</h3>
                <p></p>
                <p>Please get in touch via phone on 0800 667 843.</p>
              </div>}
            </div>
          </div>
        </div>
    </div>
    );
  }

}

export default Contact;
