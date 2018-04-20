const dev = false;
const DEV_URL = 'http://0.0.0.0:8000';
const PRODUCTION_URL = 'https:/geller.co.nz';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(DEV_URL, PRODUCTION_URL);

export default url;
