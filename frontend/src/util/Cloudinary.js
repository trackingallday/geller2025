import sha1 from 'sha1';
import request from 'superagent';


const config = {
 cloud_name:"chemical-data-app",
 api_key:"394343276293738",
 api_secret:"uS6HVagKSMEDavDc4x06HR7yzZ8"
};


class Cloudinary {

  upload(file) {
    const timestamp = Date.now();
    const keys = `timestamp=${timestamp}${config.cloud_name}`;
    const	signature = sha1(keys);
    const uploadUrl = `https://api.cloudinary.com/v1_1/${config.cloud_name}/image/upload`;

    return new Promise((resolve, reject) => {
      const req = request.post(uploadUrl);
      // TODO: mike look at this
      const data = new FormData();
      data.append('file', file);
      data.append('api_key', config.cloud_names.api_key);
      data.append('timestamp', timestamp);
      data.append('signature', signature);
      req.send(data);
      req.end((err, res) => {
        if (err) {
          reject(err);
        } else {
          resolve(res.body);
        }
      });
    });
  }
}

export default Cloudinary;
