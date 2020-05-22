import React, { Component } from 'react';
import { withRouter } from 'react-router';
import { NavLink } from 'react-router-dom';

class NotFound extends Component {

  render() {
    const { ph_number, email_address, company_name, company_address } = this.props.configs;

    let getOutOfHere;
    /* Known issue: Chrome treats New Tab as a tab, so the smallest history for a new tab is 2
                    Since it seems better to keep the user on our site if we can, increase the
                    required history count to 2. I think this is the most useful.
    */
    if (window.history && window.history.length > 2) {
      // History API is available and there is a page to go back to.
      getOutOfHere = <span>click <a href={ document.referrer || "/" } onClick={ (e) => { e.preventDefault(); window.history.back(); }}>here</a> to go to the previous page</span>
    } else {
      // History API is not available or this is the first tab, offer the home page instead.
      getOutOfHere = <span>click <NavLink to='/'>here</NavLink> to go to the home page</span>
    }

    return (
      <div>
          <div className="col-md-6">
            <div className="med-right">
              <div className="hexagon white"></div>
            </div>
            <div style={{height: '80px', width: '100%'}}></div>
        </div>
        <div className="row" style={{backgroundColor: '#FFF', paddingLeft: '30px', paddingTop: '15px', paddingBottom: '70px'}}>
          <div className="row" style={{padding: '20px 40px 70px 20px'}}>
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-12">
                  <h1 className="header">Not Found</h1>
                </div>
              </div>
              <div className="row" style={{ padding: '20px 0' }}>
                <div className="col-md-12">
                  <p>
                    The page or document you're attempting to reach seems to be missing, {getOutOfHere}, or contact us for further assistance.
                  </p>
                </div>
              </div>
              <div className="row">
                <div className="col-md-4">
                  <h3>{company_name}</h3>
                  <p>{company_address}</p>
                  <p>{ph_number}</p>
                  <p>{email_address}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

}

export default withRouter(NotFound);
