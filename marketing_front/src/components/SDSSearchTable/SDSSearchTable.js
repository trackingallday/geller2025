import React from 'react';
import serverUrl from '../../constants/serverUrl';


const SdsSearchTable = ({ products }) => {
  const [filteredProducts, setFilteredProducts] = React.useState(products);
  const [searchQuery, setSearchQuery] = React.useState('');

  React.useEffect(() => {
    setFilteredProducts(products);
  }, [products]);

  function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    if (query === '') {
      setFilteredProducts(products);
      return;
    }
    const words = query.split(' ');
    const filteredProducts = products.filter(product => {
      return words.every(word => {
        const productString = JSON.stringify(product).toLowerCase();
        return productString.includes(word);
      });
    });
    setSearchQuery(query);
    setFilteredProducts(filteredProducts);
  }

  return (
    <div className="container py-5">
      <h2 className="fw-bold text-purple mb-4">Safety Data Sheet Search</h2>

      {/* Search Inputs */}
      <div className="row mb-4">
        <div className="col-md">
          <input type="text" className="form-control rounded-pill" placeholder="Search for name, brand or use" onChange={handleSearch} />
        </div>
      </div>

      {/* Table */}
      <div className="table-responsive">
        <table className="table align-middle">
          <thead className="bg-light">
            <tr>
              <th></th>
              <th>Product Name</th>
              <th>Brand</th>
              <th>Click to download</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((item, index) => (
              <tr key={index} className="border-bottom">
                <td>
                  <img src={serverUrl + item.primaryImageLink} alt="product" className="img-fluid" style={{ maxWidth: '60px' }} />
                </td>
                <td>{item.name}</td>
                <td>{item.brand}</td>
                <td>
                  <a href={'/getsds/'+item.id} className="btn btn-info rounded-pill text-white fw-semibold px-4">
                    Download SDS
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SdsSearchTable;
