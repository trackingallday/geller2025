import React, { Component } from 'react';
import './Footer.css';

export default class Footer extends Component {
  render() {
    return (
      <footer className="text-end mt-5 py-2 pb-4 footer">
        <div>
          <h1 className="text-purple">Geller</h1>
        </div>
        <div className='text small pb-4 text-purple'>
          <span>&copy; 2025 | All rights reserved.</span>
        </div>
      </footer>
    );
  }
}
