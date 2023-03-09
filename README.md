# Imaginarium

An API.


## Live preview
Live preview is available at https://imaginarium.mbogdanowicz.com/


## API overview

Routes:
- /api/user/ -- lists all users and shows their basic data
- /api/user/\<user_pk\>/ -- shows user's detailed data
- /api/image/ -- lists all images belonging to requesting user
- /api/image/\<image_pk\>/ -- show image details
- /api/image/\<image_pk\>/templink/ -- list and create temporary links to images
- /api/templink/\<token\>/ -- expiring link to image identified by token
- /admin/ -- Django admin panel


## Development setup

Development setup is based on Docker containers with bind mounts
to project directory.

To run development containers:
```
cd ./imaginarium
docker compose build
docker compose up -d
```

Site will be available at http://localhost:8000/

Superuser is provided on startup - credentials:
login:      Admin
password:   imaginariumsiteadmin

Development setup is based on env variables stored in
./imaginarium/docker/.env.dev


## Production setup

To run production setup `cd` to main project directory:
```
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Site will be available at http://localhost/

Admin credentials are the same as in development.

For live preview nginx conatiner was replaced by nginx-proxy 
and nginx acme companion to obtain and renew LetsEncrypt certificates.





