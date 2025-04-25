# Geller Website
An app for collecting data from distributors and giving customers the chemical safety info.

## Docker Setup (New)

### Prerequisites
- Docker and Docker Compose installed on your system
- SSL certificates for HTTPS (for production)

### Development Environment
1. Clone the repository
   ```
   git clone <repository-url>
   cd geller.website
   ```

2. Build and start the Docker containers
   ```
   docker-compose up --build
   ```

3. Access the application at http://localhost:8000

### Production Environment
1. Place your SSL certificates in the `nginx/certs` directory:
   - `fullchain.pem`: Your SSL certificate chain
   - `privkey.pem`: Your SSL private key

2. Update the environment variables in `docker-compose.yml` for production settings:
   ```yml
   environment:
     - DJANGO_SETTINGS_MODULE=chemicaldatasheets.settings_docker
     - DEBUG=False
     - DJANGO_ALLOWED_HOST=geller.co.nz
     - DJANGO_SUPERUSER_USERNAME=admin
     - DJANGO_SUPERUSER_PASSWORD=your_secure_password
     - DJANGO_SUPERUSER_EMAIL=admin@example.com
   ```

3. Build and start the Docker containers
   ```
   docker-compose -f docker-compose.yml up -d
   ```

4. Access the application at https://geller.co.nz

## Legacy Deployment Method

- Run `./publish.sh` on your dev machine
- Copy the created `geller_xyz.tgz` file to the target system, where `xyz` is a unique name.
- Extract the archive on the target system, `tar xzf geller_xyz.tgz`
- Run `./deploy.sh` on the target system.
- Provided that apache is symlinked to `apache/000-geller.conf` the website will be up. 
- Be sure to copy the SQLite database into place along side `manage.py` should it not be present already.