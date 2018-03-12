import os
import subprocess

from celery import Celery
from flask import Flask
from flask_pymongo import PyMongo
from flask_restful import Resource, Api, reqparse


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['MONGO_DBNAME'] = 'wugensui'

api = Api(app)

mongo = PyMongo(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

parser = reqparse.RequestParser()
parser.add_argument('action', type=str)
parser.add_argument('video_name', type=str)


@celery.task
def track(args):
    full_path = os.path.dirname(os.path.realpath(__file__))
    analyzer_path = os.path.join(full_path, 'analyze.out')
    result_dir = os.path.join(full_path, 'results')
    video_name, ext = os.path.splitext(args['video_name'])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_path = os.path.join(result_dir, '{}.dat'.format(video_name))
    with open(result_path, "w+") as f:
        subprocess.run([analyzer_path], stdout=f)
    return 1


class WushuTracker(Resource):
    def get(self):
        args = parser.parse_args()
        video = mongo.db.video.find({'name': args['video_name']})
        # print(dir(video))
        # print(video.explain())
        if args['action'] == 'track' and args['video_name']:
            track.delay(args)
            return 0
        return 1


api.add_resource(WushuTracker, '/')

if __name__ == '__main__':
    app.run(debug=True)
