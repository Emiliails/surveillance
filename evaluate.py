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

# initialize the video stream and allow the camera sensor to warmup
vs = VideoStream(usePiCamera=1).start()
# vs = VideoStream(src=0).start()
time.sleep(2.0)

theframe = None
print('system initialized')



def test(frameCount):
    # grab global references to the video stream, output frame, and lock variables
    global vs, outputFrame, lock, theframe
    # initialize the motion detector and the total number of frames read thus far
    md = SingleMotionDetector(accumWeight=0.1)
    total = 0

    # the number of frame containing motion. This frame will be saved
    # once reach 100. Then the counter will be reset.
    motionCount = 0
    counter=0

    # loop over frames from the video stream
    while True:
        counter +=1
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        theframe = vs.read()
        if (counter==500):
            counter = 0
            # grab the current timestamp
            timestamp = datetime.datetime.now()
            # save the frame to local filesystem
            filename = timestamp.strftime(
                "%A %d %B %Y %I:%M:%S%p") + "image.jpg"
            os.chdir("/home/pi/surveillance/test/img")
            cv2.imwrite(filename, theframe)

        resized = imutils.resize(theframe, width=400)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)


        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            result = md.detect_for_test(blur)

            # check to see if motion was found in the frame
            if result is not None:
                print("motion detected")
                # the number of frame containing motion is self added
                motionCount += 1

                # save the frame every 100 motion frames
                if motionCount == 100:
                    # reset the value of motionCount
                    motionCount = 0

                    print("begin to saving")

                    # grab the current timestamp
                    timestamp = datetime.datetime.now()

                    # save the background model to local file system
                    bgmodel = md.bg
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "bgmodel.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, bgmodel.copy())

                    # reset the value of motionCount
                    motionCount = 0

                    # grab the current timestamp
                    timestamp = datetime.datetime.now()

                    # save the frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "frame.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, theframe.copy())

                    # save the resized frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "resized.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, resized.copy())

                    # save the gray frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "gray.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, gray.copy())

                    # save the blured frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "blur.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, blur.copy())

                    # save the delta frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "delta.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, result.get('delta').copy())

                    # save the thresh frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "thresh.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, result.get('thresh').copy())

                    # save the erode frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "erode.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, result.get('erode').copy())

                    # save the dilate frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "dilate.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, result.get('dilate').copy())

                    # unpack the tuple and draw the box surrounding the
                    # "motion area" on the output frame
                    (thresh, (minX, minY, maxX, maxY)) = result.get('motion')
                    cv2.rectangle(resized, (minX, minY), (maxX, maxY),
                                  (0, 0, 255), 2)

                    # save the final frame to local filesystem
                    filename = timestamp.strftime(
                        "%A %d %B %Y %I:%M:%S%p") + "final.jpg"
                    os.chdir("/home/pi/surveillance/test/img")
                    cv2.imwrite(filename, resized.copy())

        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1

if __name__ == '__main__':
    # # construct the argument parser and parse command line arguments
    # ap = argparse.ArgumentParser()
    # ap.add_argument("-f", "--frame-count", type=int, default=32,
    #     help="# of frames used to construct the background model")
    # args = vars(ap.parse_args())

    # # start a thread that will perform motion detection
    # t = threading.Thread(target=test, args=(
    #     args["frame_count"],))
    # # t.daemon = True
    # t.start()
    test(32)

# release the video stream pointer
vs.stop()