import React from "react";
import "./ArticleCol.css";

const ArticleCol = ({ image, title, body, linkClass }) => {
  const btnClass = linkClass + ' btn btn-link text-primary p-0';
  const spanClass = linkClass ? 'text-white' : 'hero2link';
  return (
    <div className="content">
        <h1 className="title">
          {title}
        </h1>
        <p>
          {body}
        </p>
        <button className={btnClass}>
          <span className={spanClass}>Find out more</span>
        </button>
    </div>
  );
};

export default ArticleCol;