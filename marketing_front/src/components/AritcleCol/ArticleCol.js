import React from "react";
import "./ArticleCol.css";

const ArticleCol = ({ image, title, body }) => {
  return (
    <div className="content">
        <h1 className="title">
          {title}
        </h1>
        <p>
          {body}
        </p>
        <button className="btn btn-link text-primary p-0">
          <span className='hero2link'>Find out more</span>
        </button>
    </div>
  );
};

export default ArticleCol;