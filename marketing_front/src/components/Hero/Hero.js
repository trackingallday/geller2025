import React from 'react';
import './Hero.css';

const Hero = ({subtitle, btnText, title, titleClass, subtitleClass, imgClass}) => {
  const tClass = titleClass ? titleClass : 'hero-title-1';
  const subTClass = subtitleClass ? subtitleClass : 'hero-subtitle';
  const imClass = imgClass ? imgClass : 'hero-image';
  return (
    <div className="hero parallax-container">
      <div className='container p-0'>
        <div className="hero-content">
          <img className='new-hero-logo' src={require('../../assets/new_geller_white.svg')}></img>
          <div className="hero-text">
            <h2 className={subTClass}>{subtitle}</h2>
            <h2 className={tClass}>
              {title}
            </h2>
            { btnText && <button className="hero-button">
              {btnText}
            </button> }
          </div>
        </div>
      </div>
      <div className={imClass + ' parallax-layer'}></div>
    </div>
  );
};

export default Hero;