import React from "react";
import serverUrl from "../../constants/serverUrl";
import "./SolutionsGrid.css";

const Solutions = ({ items }) => {
  return (
    <section className="py-5 solutions-grid-container">
      <div className="container pt-3">
        <h3 className="mb-5 text-primary solutions-heading">Solutions</h3>
        <div className="row">
          {items.map((item, index) => (
            <div key={index} className="col-md-4 mb-4" style={ { padding: "0 5px" } }>
              <img
                src={serverUrl + item.image}
                alt={item.title}
                className="img-fluid rounded mb-3"
                style={{ width: "100%", height: "250px", objectFit: "cover" }}
              />
              <h5 className="fw-bold text-primary solution-title ">{item.title}</h5>
              <p className="text-muted smaller-p">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Solutions;
