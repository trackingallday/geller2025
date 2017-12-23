const dev = true;
const DEV_URL = '0.0.0.0:8000';
const PRODUCTION_URL = '104.236.249.246:8000';
let url = PRODUCTION_URL;

if(dev) {
  url = DEV_URL;
}

console.log(DEV_URL, PRODUCTION_URL);

export default `http://${url}`
