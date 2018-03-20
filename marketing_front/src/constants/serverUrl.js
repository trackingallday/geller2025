const dev = true;
const DEV_URL = 'http://0.0.0.0:3000';
const PRODUCTION_URL = 'https://app.integraindustries.co.nz';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(DEV_URL, PRODUCTION_URL);
export const IMG_DEV_URL = 'http://0.0.0.0:8000'
export default url;
