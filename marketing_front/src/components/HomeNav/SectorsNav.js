
import React, { useState } from 'react';
import sectorStore from '../../stores/sectorsStore';
import './HomeNav.css';
import hostUrl from '../../constants/serverUrl';

const SectorsNav = ({ handleClickOutside }) => {
  const [mouseIn, setMouseIn] = useState(false);
  const sectors = sectorStore.getState().sectors.sectors;
  function handleClick(s) {
    window.location.href = '/sectors/' + s.id;
  }
  function myhandleClickOutside() {
    if (mouseIn) {
      handleClickOutside();
    }
  }
  /*
   make a full overlay behind the sectors and make it clickable
  */
  return (
    <div className="full-width-overlay py-4">
  <div className="container">
    <h5 className="text-primary mb-4">Sectors</h5>
    <div className="row">
      {sectors.map((sector, index) => (
        <div key={index}
          className="col-6 col-md-3 mb-4 d-flex flex-column align-items-center"
          onClick={() => handleClick(sector)}
          style={{ cursor: 'pointer' }}
        >
          <div className="row" style={{ width: '100%', margin: '0 auto'}}>
            <div className="col-7 text-center">
              <img
                src={hostUrl + sector.image}
                alt={sector.name}
                className=""
                style={{ objectFit: 'cover', height: '60px', width: '100%' }}
              />
            </div>
            <div className="col-5 text-center d-flex align-items-center">
              <p className="text-muted small">{sector.name}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
</div>
  );
};

export default SectorsNav;