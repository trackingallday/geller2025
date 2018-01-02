const dev = false;
const dev = true;
const DEV_URL = '0.0.0.0:8000';
const PRODUCTION_URL = 'app.integraindustries.co.nz';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(DEV_URL, PRODUCTION_URL);

export default `http://${url}`
