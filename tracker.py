import os
import subprocess

from celery import Celery
from flask import Flask
from flask_pymongo import PyMongo
from flask_restful import Resource, Api, reqparse


app = Flask(__name__)
app.config.from_object(os.environ.get('FLASK_SETTINGS_MODULE'))

api = Api(app)

mongo = PyMongo(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

parser = reqparse.RequestParser()
parser.add_argument('action', type=str)
parser.add_argument('video_name', type=str)


@celery.task
def track(video):
    full_path = os.path.dirname(os.path.realpath(__file__))
    analyzer_path = os.path.join(full_path, 'analyze.out')
    result_dir = os.path.join(full_path, 'results')
    video_name, ext = os.path.splitext(video['name'])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_path = os.path.join(result_dir, '{}.dat'.format(video_name))
    with open(result_path, "w+") as f:
        subprocess.run([analyzer_path], stdout=f)
    return 1


class WushuTracker(Resource):
    def get(self):
        args = parser.parse_args()
        videos = mongo.db.video.find({'name': args['video_name']})
        if args['action'] == 'track' and videos.count():
            video = videos[0]
            video.pop('_id')
            track.delay(video)
            return 0
        return 1


api.add_resource(WushuTracker, '/')
