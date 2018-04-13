import request from 'superagent';


const config = {
 cloud_name:"chemical-data-app",
 upload_preset: "normal",
};


class Cloudinary {

  upload(file) {
    const uploadUrl = `https://api.cloudinary.com/v1_1/${config.cloud_name}/image/upload`;

    return new Promise((resolve, reject) => {
      const req = request.post(uploadUrl);
      const data = new FormData();
      data.append('file', file);
      data.append('upload_preset', config.upload_preset);
      data.append('tags', 'browser_upload');

      req.set('X-Requested-With', 'XMLHttpRequest');
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
