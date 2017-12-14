import React, { Component } from 'react';
import DistributorPage from './components/pages/Distributor';
import LoginPage from './components/pages/Login';
import { getUserDetails } from './util/DjangoApi';
import './App.css'


class App extends Component {

  state = {
    user: null,
  }

  onLogin = (userDetails) => {
    console.log(userDetails);
    this.setState({
      user: userDetails,
    });
  }

  componentDidMount() {
    const token = localStorage.getItem('token');
    if(token) {
      getUserDetails(this.onLogin);
    }
  }

  render() {
    const { user } = this.state;
    if(!user) {
      return (<LoginPage />)
    }

    switch(user.profile.profileType) {
      case 'distributor':
        return (
          <DistributorPage user={user} />
        );
      default:
        return null;
    }

  }
}

export default App;
