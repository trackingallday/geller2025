import React from 'react';
import './Hero2.css';

const Hero2 = () => {
  return (
    <div className="hero">
      <div className="hero-content">
        <div className="hero-text">
          <h2 className="hero-subtitle"></h2>
          <h2 className="hero-title">
            Our Story
          </h2>
          <p>
            We are the hygiene solution specialists, dedicated to creating a world where people can enjoy their environments with peace of mind knowing they are safe, clean and healthy.
          </p>
          <button className="btn btn-link text-primary p-0">
            <span className='hero2link'>Find out more</span>
          </button>
        </div>
      </div>
      <div className="hero2-image"></div>
    </div>
  );
};

export default Hero2;