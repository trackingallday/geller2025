import serverUrl from '../constants/serverUrl';
import axios from 'axios';

function getData(path, callback) {
  const token = localStorage.getItem('token');
  axios.defaults.headers.common['Authorization'] = token;
  return axios.get(serverUrl + path)
    .then((response) => {
      callback(response);
    }).catch((error) => {
      console.log(error);
    });
}

function postData(path, data, callback) {
  const token = localStorage.getItem('token');
  axios.defaults.headers.common['Authorization'] = token;
  return axios.post(serverUrl + path, { data })
    .then((response) => {
      callback(response);
    }).catch((error) => {
      console.log(error);
    });
}

export function getCustomers(callback) {

  return getData('/customers_list/', (response) => {
    const customers = response.data.map((c, i) => {
      return Object.assign(c, c.user, { key: i });
    });
    callback(customers);
  });

}

export function getProducts(callback) {

  return getData('/products_list/',(response) => {
    callback(response.data);
  });

}

export function getSafetyWears(callback) {

  return getData('/safety_wears_list/',(response) => {
    callback(response.data);
  });

}

export function postNewCustomer(data, callback) {

  return postData('/new_customer/', data, callback);

}

export function postEditCustomer(data, callback) {

  return postData('/edit_customer/', data, callback);

}
