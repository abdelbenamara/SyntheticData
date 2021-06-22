[![Build Status](https://travis-ci.com/abdelbenamara/SyntheticData.svg?token=Faxx7x1Akpy5JMhYXeUC&branch=master)](https://travis-ci.com/github/abdelbenamara/SyntheticData)

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
  bash development/crontab.sh
  ```

* Open a web browser and navigate to http://localhost:5000/
  
## For production

* The application is built with [docker](https://www.docker.com/get-started)

* Before all :
  ```
  cd synthetic-data-app/
  ```
  
* To retrieve the docker image :
  ```
  docker pull abdelbenamara/synthetic-data-app
  ```
  
  * Alternatively, to build the docker image :

    ```
    docker build -t abdelbenamara/synthetic-data-app .
    ```
  
* To set up secret keys for production :
  ```
  SECRET_KEY=$(python -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export SECRET_KEY
  WTF_CSRF_SECRET_KEY=$(python -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export WTF_CSRF_SECRET_KEY
  ```
  
* To run the docker image :
  ```
  docker run -d --rm -p HOST_PORT:5000 --env-file production/env.list --name CONTAINER_NAME abdelbenamara/synthetic-data-app
  ```

* Open a web browser and navigate to ``` HOST_IP:HOST_PORT ```
