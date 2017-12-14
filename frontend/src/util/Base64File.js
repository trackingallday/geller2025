export default function base64File(file) {

   var reader = new FileReader();
   reader.readAsDataURL(file);

   return new Promise((resolve, reject) => {
     reader.onload = function () {
       resolve(reader.result);
     };
     reader.onerror = function (error) {
       reject(error);
     };
   });
  
}
