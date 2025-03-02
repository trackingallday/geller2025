import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";

const App = () => {
  return (
    <div className="container my-5">
      {/* Customer Testimonial Section */}
      <div className="row align-items-center mb-5">
        <div className="col-md-6">
          <img
            src="https://via.placeholder.com/600x350"
            alt="Customer Testimonial"
            className="img-fluid rounded"
          />
        </div>
        <div className="col-md-6">
          <h2 className="text-primary">What our customers are saying.</h2>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed diam
            nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat
            volutpat.
          </p>
          <a href="#" className="text-primary text-decoration-none">
            Find out more
          </a>
        </div>
      </div>

      {/* Cleaning Hacks Section */}
      <div className="row">
        <div className="col-md-6">
          <div className="card bg-info text-white border-0">
            <img
              src="https://via.placeholder.com/600x350"
              alt="Cleaning Hacks"
              className="card-img-top"
            />
            <div className="card-body">
              <h4>Five best Cleaning hacks</h4>
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                diam nonummy nibh euismod tincidunt ut laoreet dolore magna
                aliquam erat volutpat.
              </p>
              <a href="#" className="text-white text-decoration-none">
                Find out more
              </a>
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card bg-purple text-white border-0">
            <img
              src="https://via.placeholder.com/600x350"
              alt="Cleaning Hacks"
              className="card-img-top"
            />
            <div className="card-body">
              <h4>Five best Cleaning hacks</h4>
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                diam nonummy nibh euismod tincidunt ut laoreet dolore magna
                aliquam erat volutpat.
              </p>
              <a href="#" className="text-white text-decoration-none">
                Find out more
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Section */}
      <footer className="text-end mt-5 py-4">
        <h5 className="text-purple">Geller</h5>
        <p>&copy; 2025 | All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;
