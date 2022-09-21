import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import { BrowserRouter } from 'react-router-dom'
import { GoogleReCaptchaProvider } from 'react-google-recaptcha-v3';

ReactDOM.render(
  <GoogleReCaptchaProvider
      reCaptchaKey="6LcimBYiAAAAAGfPVreKgk5Ieg71YhFbvkJAt1MZ"
  >
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </GoogleReCaptchaProvider>
  , document.getElementById('root'));
