import React from "react";
import "./ArticleCard.css";

const ArticleCard = ({ image, title, body }) => {
  return (
<div className="card shadow-sm border-0 rounded">
  { image && <img src={image} alt={title} className="card-img-top myimg" /> }
  <div className="card-body p-4">
    <h5 className="card-title">{title}</h5>
    <div className="card-text small text-truncate-multiline">
      <p className="small">
        {body}
      </p>
    </div>
    
    <a href="#" className="btn btn-link text-primary p-0">
      Find out more
    </a>
  </div>
</div>
  );
};

export default ArticleCard;