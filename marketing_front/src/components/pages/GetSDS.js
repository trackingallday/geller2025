import React, { Component } from 'react';
import { withRouter } from 'react-router';
import superagent from 'superagent';
import { NavLink } from 'react-router-dom';


import URI from '../../constants/serverUrl';
//const URI = 'http://localhost:8000';

class GetSDS extends Component {

  state = {
    loading: false,
    result: 'unset'
  }

  onFormSubmit(e) {
    e.preventDefault();
    this.setState({loading: true})
    let data = new FormData(e.target);
    var params = {};
    data.forEach(function(value, key){
        params[key] = value;
    });
    var json = JSON.stringify(params);
    superagent.get(URI + '/sds_enquire/')
      .query({data: json})
      .set('Accept', 'application/json')
      .end((err, res) => {
        if (err) {
          this.setState({loading: false, result: 'failure'})
        } else {
          this.setState({loading: false, result: 'success'})
          window.location.replace(URI + '/product_download/' + this.props.productId + '/sds/');
        }
      });
  }

  render() {
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
        <div className="row" style={{backgroundColor: '#FFF', paddingTop: '30px', paddingBottom: '30px'}}>
          <div className="col-md-3"></div>
          <div className="col-md-6">
            <div className="well well-md">
              {this.state.result == 'unset' && !this.state.loading && <form onSubmit={(e) => this.onFormSubmit(e)}>
                <input name="productId" type="hidden" id="productId" value={ this.props.productId } />
                <div className="col-md-12">
                  <h3>Download SDS for { this.props.productName }</h3>
                  <p></p>
                    <div className="form-group">
                        <label>Name</label>
                        <input name="nameFrom" type="text" className="form-control" id="name" placeholder="Enter name" required="required" />
                    </div>
                    <div className="form-group">
                        <label>Company Name</label>
                        <input name="companyName" type="text" className="form-control" id="company" placeholder="Enter company" required="required" />
                    </div>
                    <div className="form-group">
                        <label>Email Address</label>
                        <div className="input-group">
                            <span className="input-group-addon"><span className="glyphicon glyphicon-envelope"></span>
                            </span>
                            <input name="emailFrom" type="email" className="form-control" id="email" placeholder="Enter email" required="required" /></div>
                    </div>
                </div>
                <div className="col-md-12">
                    <button type="submit" className="btn btn-primary pull-right" id="btnContactUs" style={{cursor:'pointer'}}>
                        Download</button>
                </div>
              </form>}
              {this.state.result == 'unset' && this.state.loading &&
                <div style={{paddingTop: '130px', paddingBottom: '75px'}}>
                  <div className="bouncing">
                    <img src={require('../../assets/email.png')} />
                  </div>
                </div>
              }
              {this.state.result == 'success' &&
                <div>
                  <h3>Thank you for your interest in { this.props.productName }</h3>
                  <p>Your download should begin shortly, or use <a href={URI + '/product_download/' + this.props.productId + '/sds/'}>this link</a> to download the SDS directly.</p>
                  <p>If you're unable to complete your download, reach out to us via our <NavLink to={'/contact/' + this.props.productId}>contact form</NavLink>.</p>
                </div>
              }
              {this.state.result == 'failure' &&
                <div>
                  <h3>Oh no! We were unable to complete the SDS download request</h3>
                  <p>
                    You may wish to return to the <NavLink to={'/product/' + this.props.productId}>product page</NavLink> or alternatively, use our <NavLink to={'/contact/' + this.props.productId}>contact form</NavLink> to get in touch with us.
                  </p>
                  <p>
                    We apologise for any inconvenience caused.
                  </p>
                </div>
              }
            </div>
          </div>
          <div className="col-md-3"></div>
        </div>
    </div>
    );
  }

}

export default GetSDS;
