# import the necessary packages
import os

from numpy import record
from pyimagesearch.buzzer.buzzer import destroy_buzzer, setup_buzzer, start_buzzer, stop_buzzer
from pyimagesearch.motion_detection.singlemotiondetector import SingleMotionDetector
from systeminfo import generic_info, system_info
from imutils.video import VideoStream
from flask_bootstrap import Bootstrap5
from flask import Response, request
from flask import Flask
from flask import render_template
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
import threading
import argparse
import datetime
import imutils
import time
import cv2

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
# creating a lock
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

# register a blueprint to show system info
app.register_blueprint(system_info)
# instanzlize the Bootstrap5 class
bootstrap = Bootstrap5(app)

# initialize a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


# database model
class Records(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return 'Record %r' % self.id

# initialize the buzzer
setup_buzzer()

# initialize the video stream and allow the camera sensor to warmup
vs = VideoStream(usePiCamera=1).start()
# vs = VideoStream(src=0).start()
time.sleep(2.0)

@app.route("/")
def index():
    # get system info dict
    system_info = generic_info()
    # return the rendered template
    return render_template("index.html",system_info=system_info)

@app.route("/records")
def records():
    page = request.args.get('page', 1, type=int)
    pagination = Records.query.order_by(Records.id.desc()).paginate(page, per_page=5)
    # pagination = Records.query.paginate(page, per_page=10)
    records = pagination.items
    titles = [('id', '#'), ('image_name', 'Image'), ('date_created', 'Create Time')]
    return render_template("records.html", records=records, titles=titles, Records=Records, pagination=pagination)


def detect_motion(frameCount):
    # grab global references to the video stream, output frame, and lock variables
    global vs, outputFrame, lock

    # initialize the motion detector and the total number of frames read thus far
    md = SingleMotionDetector(accumWeight=0.1)
    total = 0

    # the number of frame containing motion. This frame will be added to the database
    # once reach 100. Then the counter will be reset.
    motionCount = 0

    # the status of the buzzer
    buzzering = False

    # loop over frames from the video stream
    while True:
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime(
            "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            motion = md.detect(gray)

            # check to see if motion was found in the frame
            if motion is not None:
                #start buzzering
                if not buzzering:
                    start_buzzer()
                    buzzering = True
                # unpack the tuple and draw the box surrounding the
                # "motion area" on the output frame
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY),
                    (0, 0, 255), 2)
                # the number of frame containing motion is self added
                motionCount += 1
                
                # save the frame to database every 100 motion frames
                if motionCount == 100:
                    # reset the value of motionCount
                    motionCount = 0

                    # save the frame and filename to local filesystem & database, respectively
                    filename = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")+".jpg"
                    os.chdir("/home/pi/surveillance/static/img")
                    cv2.imwrite(filename,frame.copy())
                    new_record = Records(image_name=filename)
                    try:
                        db.session.add(new_record)
                        db.session.commit()
                    except:
                        print('There was an issue adding your record')
            else:
                # stop buzzering
                if buzzering:
                    stop_buzzer()
                    buzzering = False

        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1
        
        # acquire the lock, set the output frame, and release the lock
        with lock:
            outputFrame = frame.copy()

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

        # check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
        help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
        help="# of frames used to construct the background model")
    args = vars(ap.parse_args())

    # start a thread that will perform motion detection
    t = threading.Thread(target=detect_motion, args=(
        args["frame_count"],))
    t.daemon = True
    t.start()

    # start the flask app
    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)
        
# release the video stream pointer
vs.stop()

# release the buzzer
destroy_buzzer()