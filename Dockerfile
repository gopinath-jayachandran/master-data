## Use an official Python runtime as a parent image
#FROM python:3.9-slim
#
## Set the working directory in the container
#WORKDIR /app
#
## Copy the current directory contents into the container at /app
#COPY . /app
#
## Install any needed packages specified in requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#
## Make port 5000 available to the world outside this container
#EXPOSE 5000
#
## Run main.py when the container launches
#CMD ["flask", "run", "--host=0.0.0.0"]

FROM python:3.8-slim


RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

CMD ["flask", "run"]
