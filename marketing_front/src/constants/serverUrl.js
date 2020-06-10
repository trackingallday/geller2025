const dev = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
const DEV_URL = 'http://0.0.0.0:8000';
const PRODUCTION_URL = 'https://geller.co.nz';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(DEV_URL, PRODUCTION_URL);
export const IMG_DEV_URL = 'http://0.0.0.0:8000'
export default url;
