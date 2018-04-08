import xhr from 'xhr';


const accessToken = 'pk.eyJ1IjoiY2hlbXNhcHAiLCJhIjoiY2pheWdzNjd6MTJnbDMzczczbG92ZG15ayJ9.sqO7Za5EYpuhj6REKyneFA';
const endpoint = 'https://api.mapbox.com';
const source = 'mapbox.places';

export default function search(query='', callback) {
  const searchTime = new Date();
  const uri = `${endpoint}/geocoding/v5/${source}/${encodeURIComponent(query)}.json?access_token=${accessToken}&country=NZ`;
  xhr({
    uri: uri,
    json: true
  }, (err, res, body) => {
    callback(err, res, body, searchTime);
  });
}
