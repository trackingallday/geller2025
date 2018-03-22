
   import React, { Component } from 'react';
   import '../App.css'
   import CoverNav from './CoverNav';
   import { withRouter } from 'react-router'


   class MobileNav extends Component {

     state = {
       show: false,
     }

     toggleShow = () => {
       this.setState({
         show: !!this.state.show,
       })
     }

     render() {
       return (
         <div className="row mobile-nav" style={ {height: '52px', backgroundColor: '#fff' }}>
           <div className="col-md-12">
              <nav className="navbar navbar-dark bg-dark">
                <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarToggleExternalContent"
                  aria-controls="navbarToggleExternalContent" aria-expanded="false" aria-label="Toggle navigation" style={{}}>
                  <img src={require('../assets/hamburger-icon.png')} style={{width: '28px'}}/>
                </button>
              </nav>
              <div className="pos-f-t" style={{backgroundColor: '#fff', zIndex: '9999'}}>
               <div className="collapse row" id="navbarToggleExternalContent">
                 <nav className="nav flex-column front" style={{backgroundColor: '#fff', width:'100%'}}>
                   <a className="nav-link" href="/">Home</a>
                   <a className="nav-link" href="/our_products/all">Products</a>
                   <a className="nav-link" href="/support">Support</a>
                   <a className="nav-link" href="/news">News</a>
                   <a className="nav-link" href="/about">About</a>
                 </nav>
               </div>
            </div>
           </div>
          </div>
       );
     }
   }

   export default MobileNav
