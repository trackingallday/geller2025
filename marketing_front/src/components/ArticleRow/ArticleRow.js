import React from "react";
import "./ArticleRow.css";

const ArticleRow = ({ image, title, body, linkColor, bgColor, pColor, titleColor }) => {
  
  return (
<div className="card border-0 rounded" style={{ color: titleColor, backgroundColor: bgColor }}>
  { image && <img src={"http://localhost:8000" + image} alt={title} className="card-img-top myimg" /> }
  <div className="card-body p-4" style={{ color: titleColor, backgroundColor: bgColor }}>
    <h1 className="card-title">{title}</h1>
    <div className="card-text small text-truncate-multiline">
      <p style={{ color: pColor }} className="article-row-p">
        {body}
      </p>
    </div>
    
    <a href="#" className="btn btn-link text-primary p-0" style={{ color: linkColor }}>
      <span style={{color: linkColor }}>Find out more</span>
    </a>
  </div>
</div>
  );
};

export default ArticleRow;