import numpy as np
import cv2
import argparse
import datetime
import imutils
import time
import pandas as pd

class Vid:
    def __init__(self, videoPath, winName):
        self.cap = cv2.VideoCapture(videoPath)
        if self.cap.isOpened():
            self.startFrame = 0
            self.spf = int((1/self.cap.get(5))*1000)
            #self.cap.set(1,self.startFrame)
            self.winName = winName
            self.length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cv2.namedWindow(self.winName)
            self.min = 0
            self.timeFrozen = 0
            self.text = ''
            self.capError = False
            self.freezeFile = open('freezes.txt','w')
            self.isFrozen = False
            self.threshold = 20
            self.length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.index = 0
            self.freezeThreshold = 1000
        else:
            self.capError = True


    def trackBar(self,winName,trackName,min, max):
        cv2.createTrackbar(trackName, winName,min,max,
        lambda x: self.picFrame(x, self))

    def picFrame(x, frame, self):
        self.startFrame = frame
        self.cap.set(1,self.startFrame)
        self.isFrozen = False
        self.timeFrozen = 0

        '''
    def setByTime(self):
        self.cap.set(0,self.timeToMilli(self.csv['Time'][self.index]))
        self.index+=1
        '''

    def timeToMilli(self, s):
        s = s.replace(".",":")
        hours, minutes, seconds, milliseconds = s.split(":")
        return int(hours)*60*60*1000 + int(minutes)*60*1000 + int(seconds)*1000 + int(milliseconds)


    def run(self):
        noROI = True
        noPrevFrame = True
        noPrevThresh = True
        while(self.cap.isOpened()):
            #Get frame
            cur = time.perf_counter()
            ret, frame = self.cap.read()
            if not ret:
                break
            print(time.perf_counter() - cur)
            # Create ROI if not done yet
            # Otherwise grab ROI
            if noROI:
                r = cv2.selectROI(frame)
                cv2.destroyWindow("ROI selector")
                noROI = False
                continue
            else:
                imgROI = frame[int(r[1]):int(r[1]+r[3]),int(r[0]):int(r[0] + r[2])]

            #Make gray and blur
            gray = cv2.cvtColor(imgROI, cv2.COLOR_BGR2GRAY)
            #gray = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            #    cv2.THRESH_BINARY,30,15)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            cv2.imshow(self.winName,gray)


            if noPrevFrame:
                prevFrame = gray
                noPrevFrame = False
                continue
            else:
                if noPrevThresh:
                    prevThresh = self.calcInitThresh(gray, prevFrame)
                    noPrevThresh = False
                    continue
                else:
                    movingPxls, prevThresh, prevFrame = self.calcMovingPixels(gray, prevFrame, prevThresh)

            # Moving or frozen?
            if movingPxls>70:
                self.text = 'move'
                self.timeFrozen = 0
                if self.isFrozen:
                    self.isFrozen = False
                    self.freezeFile.write('end freeze: ' + str(self.milliToTime(self.cap.get(0))) + '\n')
            else:

                if self.checkFreeze() and not self.isFrozen:
                    self.isFrozen = True
                    self.freezeFile.write('freeze: ' + str(self.milliToTime(self.cap.get(0))) + '\n')
                    self.text = 'freeze'


            # Write freeze/move on screen
            cv2.putText(prevThresh, self.text, (10, 50),cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 2)
            cv2.putText(prevThresh, str(self.timeFrozen), (100, 50),cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 2)

            #cv2.putText(prevThresh, self.csvText, (10, 75),cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 2)
            cv2.putText(prevThresh, str(self.startFrame), (10,95), cv2.FONT_HERSHEY_SIMPLEX, .5, (255,255,255),2)

            #cv2.putText(prevThresh, str(self.csv['Time'][self.index-1]), (10,110), cv2.FONT_HERSHEY_SIMPLEX, .5, (255,255,255),2)
            cv2.putText(prevThresh, self.milliToTime(self.cap.get(0)), (10,125), cv2.FONT_HERSHEY_SIMPLEX, .5, (255,255,255),2)

            cv2.imshow('thresh',prevThresh)
            # Get next frame
            self.startFrame+=1

            if cv2.waitKey(self.spf) & 0xFF == ord('q'):
                break

    def calcInitThresh(self, frame, prevFrame):
        frameDelta = cv2.absdiff(frame, prevFrame)
        return cv2.threshold(frameDelta, self.threshold, 255, cv2.THRESH_BINARY)[1]

    def calcMovingPixels(self, frame, prevFrame, prevThresh):
        #Start motion detection
        # compute the absolute difference between the current frame and
        # previous frame
        frameDelta = cv2.absdiff(frame, prevFrame)
        thresh = cv2.threshold(frameDelta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        #thresh = cv2.adaptiveThreshold(frameDelta,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
        #    cv2.THRESH_BINARY,21,5)


        diff = cv2.subtract(thresh, prevThresh)
        movingPxls = cv2.countNonZero(diff)
        return movingPxls, thresh, frame

    def checkFreeze(self):
        if self.timeFrozen < self.freezeThreshold:
            self.timeFrozen+=self.spf
            return False
        else:
            self.timeFrozen+=self.spf
            return True

    def close(self):
        self.freezeFile.close()
        self.cap.release()
        cv2.destroyAllWindows()

    def milliToTime(self, milliseconds):
        seconds=(milliseconds/1000)%60
        minutes=(milliseconds/(1000*60))%60
        hours=(milliseconds/(1000*60*60))%24
        return str(int(hours)) + ":" + str(int(minutes)) + ":" + str(seconds)

def main():
    vid = Vid('FR_con1.avi','vid')
    if not vid.capError:
        vid.trackBar('vid','frameNumber',0, vid.length)
        vid.run()
        vid.close()


main()
