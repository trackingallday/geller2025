import React from 'react';
import './Hero3.css';

const Hero3 = (props) => {
  const { title, subtitle } = props;
  return (
    <div className="hero-3">
      <div className="hero-3-content">
        <div className="hero-3-text">
          <h2 className="hero-3-title">
            {title}
          </h2>
          <p>
            {subtitle}
          </p>
          <button className="btn btn-link text-primary p-0">
            <span className='hero-3link'>Find out more</span>
          </button>
        </div>
      </div>
      <div className="hero-3-image"></div>
    </div>
  );
};

export default Hero3;