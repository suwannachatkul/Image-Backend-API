# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Copy the current directory contents into the container at /app
COPY . /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory to /app
WORKDIR /app/image_backend

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=image_backend.settings_prod
ENV PYTHONUNBUFFERED 1
ENV DATABASE_PORT 5432

# Following are other env needed to add during run command
# or manually add them here
# ENV POSTGRES_DB_NAME myimage
# ENV POSTGRES_DB_USER myimageuser
# ENV POSTGRES_DB_HOST postgres-host
# ENV POSTGRES_DB_PASSWORD postgres-password
# ENV SECRET_KEY secret_key
# ENV AWS_ACCESS_KEY_ID
# ENV AWS_SECRET_ACCESS_KEY

# Expose port 8000 for the Django app
EXPOSE 8000

# Start the Django app using Gunicorn
CMD ["gunicorn", "image_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
