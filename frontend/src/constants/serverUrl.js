const dev = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
const DEV_URL = 'http://0.0.0.0:8000';
const PRODUCTION_URL = 'https://geller.co.nz';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(url);

export default url;
