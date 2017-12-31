import React, { Component } from 'react';
import DistributorPage from './components/pages/Distributor';
import AdminPage from './components/pages/Admin';
import CustomerPage from './components/pages/Customer';
import LoginPage from './components/pages/Login';
import { getUserDetails } from './util/DjangoApi';
import './App.css'


class App extends Component {

  state = {
    user: null,
    started: false,
  }

  onLogin = (userDetails) => {
    this.setState({
      user: userDetails,
      started: true,
    });
  }

  componentDidMount() {
    const token = localStorage.getItem('token');
    if(token && token !== "null") {
      getUserDetails(this.onLogin);
    } else {
      this.setState({
        started: true,
      });
    }
  }

  render() {
    const { user, started } = this.state;

    if(!started) {
      return (<div />);
    }

    if(!(user && user.profile)) {
      return (<LoginPage onLogin={this.onLogin} />)
    }

    switch(user.profile.profileType) {
      case 'admin':
        return (
          <AdminPage user={user} />
        );
      case 'distributor':
        return (
          <DistributorPage user={user} />
        );
      case 'customer':
        return (
          <CustomerPage user={user} />
        );
      default:
        return (
          <CustomerPage user={user} />
        );
    }

  }
}

export default App;
