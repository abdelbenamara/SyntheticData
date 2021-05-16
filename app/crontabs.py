from flask_crontab import Crontab

from app import app
from .utils import clean_create_dir

crontab = Crontab(app)


@crontab.job(minute="30", hour="3")
def delete_all_resources_and_results():
    clean_create_dir(app.config['RESOURCES'], app.instance_path)
    clean_create_dir(app.config['RESULTS'], app.instance_path)
