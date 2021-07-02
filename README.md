[![Build Status](https://travis-ci.com/abdelbenamara/SyntheticData.svg?token=Faxx7x1Akpy5JMhYXeUC&branch=master)](https://travis-ci.com/github/abdelbenamara/SyntheticData)

# Synthetic Data Application

## Features

#### Good to know

* You have a complete set of files ready to be used in the [example folder](https://github.com/abdelbenamara/SyntheticData/tree/master/synthetic-data-app/example).

* When you generate a synthetic dataset, the evaluation of this one is done automatically.

### Generation of synthetic dataset

* You need a structured dataset

* You must specify the following parameters :

  * samples
  * epochs
  * names
  * categories
  * correlees
  * drop
  * unnamed
  * compare

* You must specify correlations between data of columns two by two if necessary

### Evaluation of synthetic dataset

* You need a structured dataset

* You must specify the following parameters :

  * names
  * categories
  * correlees
  * drop
  * unnamed
  * compare

* You need a synthetic dataset

## Development use

* The project is based on [python 3.8](https://www.python.org/downloads/release/python-380/)

* Before all :
  ```
  cd synthetic-data-app/
  ```

* Set up a virtual environnement (e.g. with [virtualenv](https://virtualenv.pypa.io/en/latest/)) :
  ```
  bash development/setup.sh
  ```
      
* Run in your activated virtual environnement terminal :
  ```
  bash development/start.sh
  ```

* Optionally, you can use scheduled jobs (e.g. with [flask-crontab](https://github.com/frostming/flask-crontab)) :
  ```
  bash development/crontab.sh
  ```

* Open a web browser and navigate to http://localhost:5000/
  
## Production use

* The application is built with [docker](https://www.docker.com/get-started)

* Before all :
  ```
  cd synthetic-data-app/
  ```
  
* Build the docker image :
  ```
  docker build -t synthetic-data-app .
  ```
  
* Set up secret keys for production :
  ```
  SECRET_KEY=$(python -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export SECRET_KEY
  WTF_CSRF_SECRET_KEY=$(python -c 'import random, string; print("".join([random.choice(string.printable) for _ in range(24)]));')
  export WTF_CSRF_SECRET_KEY
  ```
  
* Run the docker image :
  ```
  docker run -d --rm -p HOST_PORT:5000 --env-file production/env.list --name CONTAINER_NAME abdelbenamara/synthetic-data-app
  ```

* Open a web browser and navigate to ``` HOST_IP:HOST_PORT ```
