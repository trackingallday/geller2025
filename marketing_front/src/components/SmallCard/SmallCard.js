import React from "react";
import "./SmallCard.css";

const SmallCard = ({ image, title, body }) => {
  return (
<div className="card shadow-sm border-0 rounded newsmallcard">
  { image && <img src={image} alt={title} className="card-img-top myimg" /> }
  <div className="card-body px-4 pb- pt-2">
    <div className="card-title">
      <span className="smallcardtitle"
        style={{color: "#757575", fontSize: "1.1rem", letterSpacing: "-0.1px"}}>
        {title}
      </span>
    </div> 
    <div className="small text-truncate-multiline"
      style={{color: "#757575", fontSize: "0.8rem", letterSpacing: "-0.1px"}}>
      {body}
    </div>
  </div>
</div>
  );
};

export default SmallCard;