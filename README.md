# chemicaldataapp
an app for collecting data from distributors and giving customers the chemical safety info

# Deploying to a server

- Run `./publish.sh` on your dev machine
- Copy the created `geller_xyz.tgz` file to the target system, where `xyz` is a unique name.
- Extract the archive on the target system, `tar xzf geller_xyz.tgz`
- Run `./deploy.sh` on the target system.
- Provided that apache is symlinked to `apache/000-geller.conf` the website will be up. 
- Be sure to copy the SQLite database into place along side `manage.py` should it not be present already.