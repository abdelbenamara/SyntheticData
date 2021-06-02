[![Build Status](https://travis-ci.com/abdelbenamara/SyntheticData.svg?branch=master)](https://travis-ci.com/github/abdelbenamara/SyntheticData)

# Synthetic Data Application

## For development

* The project is based on [python 3.8](https://www.python.org/downloads/release/python-380/)

* Before all :
  ```
  cd synthetic-data-app/
  ```

* To set up a virtual environnement (e.g. with [virtualenv](https://virtualenv.pypa.io/en/latest/)) :
  ```
  bash development/setup.sh
  ```
      
* To run in your activated virtual environnement terminal :
  ```
  bash development/start.sh
  ```

* Optionally, to use scheduled tasks (e.g. with [flask-crontab](https://github.com/frostming/flask-crontab)) :
  ```
  bash development/cron.sh
  ```

* Open a web browser and navigate to http://localhost:5000/
  
## For production

* The application use [docker](https://www.docker.com/get-started)

* Before all :
  ```
  cd synthetic-data-app/
  ```
  
* To retrieve the docker image :
  ```
  docker pull abdelbenamara/synthetic-data-app:latest
  ```
  
* To set up secret keys for production :
  ```
  SECRET_KEY=$(pyhton -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export SECRET_KEY
  WTF_CSRF_SECRET_KEY=$(pyhton -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export WTF_CSRF_SECRET_KEY
  ```
  
* To run the docker image :
  ```
  docker run -d --rm -p HOST_PORT:5000 --env-file env.list --name CONTAINER_NAME abdelbenamara/synthetic-data-app
  ```

* Open a web browser and navigate to ``` HOST_IP:HOST_PORT ```
