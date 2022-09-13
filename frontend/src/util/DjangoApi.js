import serverUrl from '../constants/serverUrl';
import axios from 'axios';


const fail = (err) => console.warn(err);

function getData(path, onSuccess, onFail=fail) {
  const token = localStorage.getItem('token');
  axios.defaults.headers.common['Authorization'] = token;
  return axios.get(serverUrl + path)
    .then((response) => {
      return onSuccess(response);
    }).catch((error) => {
      onFail(error);
      onSuccess({data:[]});
    });
}

function postData(path, data, onSuccess, onFail=null) {
  if (!onFail) {
    onFail = fail
  }
  const token = localStorage.getItem('token');
  axios.defaults.headers.common['Authorization'] = token;
  return axios.post(serverUrl + path, { data })
    .then((response) => {
      onSuccess(response);
    }).catch((error) => {
      onFail(error);
    });
}

function addKeys(records) {
  return records.map((r, i) => {
    return Object.assign(r,{ key: i, rowKey: i });
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

export function getMarkets(callback) {

  return getData('/markets_list/', (response) => {
    const items = response.data.map((c, i) => {
      return Object.assign(c, c.user, { key: i });
    });
    callback(items);
  });

}

export function getCategories(callback) {

  return getData('/categories_list/', (response) => {
    const items = response.data.map((c, i) => {
      return Object.assign(c, c.user, { key: i });
    });
    callback(items);
  });

}

export function getSizes(callback) {

  return getData('/sizes_list/', (response) => {
    const items = response.data.map((c, i) => {
      return Object.assign(c, c.user, { key: i });
    });
    callback(items);
  });

}

export function getProducts(callback) {

  return getData('/list_products/',(response) => {
    callback(addKeys(response.data));
  });

}

export function getDistributors(callback) {

  return getData('/distributors_list/',(response) => {
    const dudes = response.data.map((c, i) => {
      return Object.assign(c, c.user, { key: i });
    });
    callback(dudes);
  });

}

export function getSafetyWears(callback) {

  return getData('/safety_wears_list/',(response) => {
    callback(addKeys(response.data));
  });

}

export function postNewDistributor(data, callback, onFail=null) {
  return postData('/new_distributor/', data, callback, onFail);
}

export function postEditDistributor(data, callback) {
  return postData('/edit_distributor/', data, callback);
}

export function postNewCustomer(data, callback, onFail=null) {
  return postData('/new_customer/', data, callback, onFail);
}

export function postEditCustomer(data, callback, onFail=null) {
  return postData('/edit_customer/', data, callback, onFail);
}

export function postNewProduct(data, callback, onFail=null) {
  return postData('/new_product/', data, callback, onFail);
}

export function postEditProduct(data, callback, onFail=null) {
  return postData('/edit_product/', data, callback, onFail);
}

export function getUserDetails(onSuccess, onFail=fail) {
  return getData('/user_details/', (res) => onSuccess(res.data), (err) => onFail(err));
}

export function getProductsMap(onSuccess, onFail=fail) {
  return getData('/list_products_map/', (res) => onSuccess(res.data), (err) => onFail(err));
}

export function getCustomersTable(onSuccess) {
  return getData('/customers_table/', onSuccess);
}

export function getCustomersTableAdmin(onSuccess) {
  return getData('/customers_table_admin/', onSuccess);
}

export function postCustomerSheet(customer_id, onSuccess) {
  return postData('/printout/', { customer_id }, onSuccess);
}

export function getCustomerSheet(onSuccess) {
  return getData('/printout/', onSuccess);
}

export function postLogin(username, password, onSuccess, onFail=fail) {
  return axios.post(serverUrl + '/get_auth_token/', { username, password })
    .then((response) => {
      localStorage.setItem('token', `Token ${response.data.token}`);
      return getUserDetails(onSuccess, onFail);
    }).catch((error) => {
      onFail(error);
    });
}
