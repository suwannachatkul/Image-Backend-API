# Image Management API

Image Backend is a project developed based on Django Rest Framework and provides API endpoints for managing and serving images.  
Also included server-side cookies-based authentication using JWT tokens.

## Getting Started

### Prerequisites

- Python 3.x
- Pipenv

### Installing

1. Clone this repository


2. Navigate to the project directory


3. Install dependencies using Pipenv:

    ```
    pipenv install -r ./requirements.txt
    ```

### Running the server

1. Activate the Pipenv shell:

    ```
    pipenv shell
    ```

2. Run the server:

    ```
    python manage.py runserver
    ```

The server should now be running at http://localhost:8000/.

## API Endpoints

The following endpoints are available:

### Authentication Endpoints

| Endpoint | HTTP Method | Data | Description |
| -------- | ----------- | --------------- | ----------- |
| /image_api/auth/login/ | POST | **Body**: {"username": string, "password": string} | Obtain JWT token and set cookies for authentication. |
| /image_api/auth/refresh/ | POST | - | Obtain and Refresh new Token cookies |
| /image_api/auth/logout/ | POST | - | Delete Token cookies |

### Image API endpoints

| Endpoint | HTTP Method | Data | Description |
| -------- | ----------- | --------------- | ----------- |
| /image_api/image/ | GET | **QueryParams**: ["tags": string, "created_date": datetime, "created_date__after": datetime, "created_date__before": datetime, "random": bool, "limit": int, "offset": int] | Get list of images |
| /image_api/image/upload | POST | **Body**: {"image": file, "title": string, "description": string, "tags": [string1, string2]} <br /> **QueryParams**: ["file_ext": [ jpg, png, webp ]] | Upload a new image |
| /image_api/image/:id/ | GET | - | Get details about a specific image by id |
| /image_api/image/:id/update | PUT,PATCH | **Body**: {"title": string, "description": string, "tags": [string1, string2]} | Update details of an image |
| /image_api/image/:id/delete | DELETE | - | Delete an image |
| /image_api/image/tag/ | GET | - | Get a list of all tags |


### Example Usage

Obtain a token for authentication
```
curl -X POST \
  http://localhost:8000/image_api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "password": "your_password"
}'
```

Get a list of all images
```
curl -X GET \
  http://localhost:8000/image_api/image/ \
  -H 'Authorization: Bearer <your_token_here>'
```

Get a list of images with tags "landscape" or "Tokyo" with limit to 10
```
curl -X GET \
  http://localhost:8000/image_api/image/?tags=landscape&tags=Tokyo&limit=10 \
  -H 'Authorization: Bearer <your_token_here>'
```

Get a list of images that created between 20230501 to 20230530
```
curl -X GET \
  http://localhost:8000/image_api/image/?created_date__after=20230501&created_date__before=20230530 \
  -H 'Authorization: Bearer <your_token_here>'
```

To upload a new image with change format to webp
```
curl -X POST \
  http://localhost:8000/image_api/image/upload/?file_ext=webp \
  -H 'Authorization: Bearer <your_token_here>' \
  -H 'Content-Type: application/json' \
  -F 'image=@path/to/image.jpg' \
  -F 'title=My Image Title' \
  -F 'description=This is an image description' \
  -F 'tags=["tag1", "tag2"]'
```

Get details about a specific image by id
```
curl -X GET \
  http://localhost:8000/image_api/image/:id/ \
  -H 'Authorization: Bearer <your_token_here>'
```

Update an image info
```
curl -X PATCH \
  http://localhost:8000/image_api/image/:id/update \
  -H 'Authorization: Bearer <your_token_here>' \
  -H 'Content-Type: application/json' \
  -F 'title=My New Image Title' \
  -F 'description=This is an image updated description' \
  -F 'tags=["tag1", "tag2"]'
```

Get a list of all tags
```
curl -X GET \
  http://localhost:8000/image_api/image/tag/ \
  -H 'Authorization: Bearer <your_token_here>'
```

## Tests

```
python manage.py test --settings=image_backend.settings_test
```