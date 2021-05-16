# Synthetic_Data

## Setup project
* Use virtual environnement 
  * For example with [virtualenv](https://virtualenv.pypa.io/en/latest/) :
    * Open terminal and execute :   
      ```
      bash venv.sh
      ```
    * You can also do manually :
      ```
      pip install virtualenv
      virtualenv venv
      source venv/bin/activate
      ```
* In virtual environnement activated terminal execute :
  ```
  bash first.sh
  ```
* You can also do manually :
  ```
  pip install -r requirements.txt
  pip install dpwgan/ --use-feature=in-tree-build
  ```

## Launch app
* In virtual environnement activated terminal execute :
  ```
  bash start.sh
  ```
* You can also do manually :
  ```
  export FLASK_ENV=development
  flask run
  ```
* Open a web browser and navigate to http://127.0.0.1:5000/

## Optional
* You can schedule tasks with [flask-crontab](https://github.com/frostming/flask-crontab)
