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

Development setup is based on Django test server.
Connection with local code is maintained via bind mounts.

To spin development containers:
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

Production setup is based on nginx and gunicorn. Bind mounts were replaced
with volumes.

To spin production containers:
```
cd ./imaginarium
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Site will be available at http://localhost/ (port 80).

Admin credentials are the same as in development.

For live preview nginx conatiner was replaced by nginx-proxy 
and nginx acme companion to obtain and renew LetsEncrypt SSL certificates.


## Testing

Test with Django's standard `python manage.py test`.
No need to run tests within Docker containers.

Make sure to `pip install` requirements either locally
or in virtual enviroment before testing.


## Tech stack:
- Django
- Django Rest Framework
- Sorl thumbnail
- Redis
- Celery
- Nginx
- Docker





