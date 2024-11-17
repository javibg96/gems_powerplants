
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Set environment variables
ENV AWS_DEFAULT_REGION=eu-west-1

# Copy the current directory contents into the container at /usr/src/app
COPY . /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Make port 80 available to the world outside this container
EXPOSE 8888


# Run app.py when the container launches
CMD ["python", "./poweplants_main.py"]


