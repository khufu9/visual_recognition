"""
	SURVEILLENCE SCRIPT
	----------------------------------------------------------
	This script taps into an OpenCV camera stream which can be 
	used to survey a location. The script perform face detect-
	ion and is able to track any number of detected targets. 
		
"""

__version__ = 0.1

import os
import cv
import numpy
import math
import recon
import datetime
import time

capdevice =1 # 0 for integrated cam 1 for usb-cam

class Target:
	def __init__(self,HaarArea):
		self.__id=str(datetime.datetime.now())
		self.__rect=HaarArea[0]
		self.__fv=[HaarArea[1],HaarArea[1]] # feature vector
		self.__weight=1.0
		self.__trajectory=(0.0,0.0)
		self.__photo=None
		print "> New target created " + self.__id

	def id(self):
		return self.__id
	def get_trajectory(self):
		return self.__trajectory 
	def get_pos(self):
		return (self.__rect[0],self.__rect[1])
	def width(self):
		return self.__rect[2]
	def height(self):
		return self.__rect[3]

	def get_score(self,gain=0.9):
		return sum(self.__fv)*gain

	def update(self,HaarArea):
		"""
		Updates the
		""" 
		cvrect = HaarArea[0]
		self.__trajectory = (self.__rect[0]-cvrect[0], self.__rect[1]-cvrect[1])
		self.__rect=HaarArea[0]
		if len(self.__fv) < 10:
			self.__fv.append( HaarArea[1] )
		else:
			self.__fv = [HaarArea[1]] + self.__fv[0:9]

	def distance(self, cvrect):
		return numpy.sqrt(abs(self.__rect[0]-cvrect[0])+abs(self.__rect[1]-cvrect[1]))

	def fade(self,gain=0.9):
		for i in xrange(1,len(self.__fv)):
			self.__fv[i] = self.__fv[i]-1.0/10.0
		return sum(self.__fv)*gain

class Tracking:
	def __init__(self):
		self.targets=list()
		self.foci=list()
		self.discard_threshold = 0.0
		self.frmt = '%H:%M:%S'
		self.timer = time.time
		self.tick = self.timer()
		self.dt = 0.0

	def add_target(self,HaarArea):
		self.foci.append(HaarArea)

	def fade_all(self,gain=0.9):
		for target in self.foci:
			score = target.fade()
			if score < self.discard_threshold:
				print "> Target "+target.id()+" removed"
				self.foci.remove(target)
			else:
				print target.id() + ":: "+str(score)


	def query(self,HaarArea):
		"""
		An unknown is a CVRect (top_left_x, top_left_y, width, height)
		"""	
		urect = HaarArea[0]
		select = None		
		for target in self.foci:
			if target.distance(urect) < 10.0:
				if select != None:
					if select.get_trajectory() > target.get_trajectory():
						select = target
				else:
					select = target

		# compute FPS
		self.dt = self.timer() - self.tick
		self.tick = self.timer()

		if select != None:
			#print "Updated target: " + select.id()
			select.update(HaarArea)
			return select.id()
		else:
			self.add_target(Target(HaarArea))
			return ""





class Scan:

	def __init__(self,wn="Camera view"):
		self.windowname = wn
		self.capture = None
		self.sounds = dict()
		self.targets = []
		self.currentface = None
		self.selected = None
		self.selectedimg = None
		self.faceCascade = cv.Load("./haarcascade_frontalface_alt.xml")
		self.font =  cv.InitFont( cv.CV_FONT_HERSHEY_SIMPLEX, 0.4, 0.4, 0.0, 1, cv.CV_AA )

		
	"""
	DESCRIPTION:
	Attempts to setup a capture from the given url or device number. Otherwise, tries 
	the default web cam device
	"""
	def startCapture(self,url="",device=0):
		if len(url) > 0:
			self.capture = cv.CreateCameraCapture(url)
			if cv.GetCaptureProperty(self.capture, cv.CV_CAP_PROP_FPS) <= 0.0:
				print "!! Unable to connect to: " + str(url)
				#offline()
				self.capture = None
		else:
			self.capture = cv.CreateCameraCapture(device)
			if cv.GetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH) <= 0.0:
				print "!! No camera found on ID: " + str(device)
				#offline()
				self.capture = None

	"""
	DESCIPTION:
	Starts a window and resize it to match images taken from the capture
	"""
	def startWindow(self):

		targets = []

		img = cv.QueryFrame(self.capture)
		cv.NamedWindow(self.windowname,1)
		cv.ResizeWindow(self.windowname, img.width, img.height)
	
	"""
	DESCRIPTION:
	Destroys and active window
	"""
	def killWindow(self):
		cv.DestroyWindow(self.windowname)	

	"""
	DESCRIPTION:
	Puts the string in image at starting pixel given by point with cv-color rgb
	"""
	def write(self,img,point,string,rgb=(255,255,255)):
		cv.PutText( img, string, point, self.font, cv.RGB(rgb[0],rgb[1],rgb[2]))

	def haarScan(self,comprimg):
		haarScale = 1.2
		minNeighbors = 2
		haarFlags = 0
		minTargetSize = (20,20)
		
		suspects = cv.HaarDetectObjects( comprimg, self.faceCascade, cv.CreateMemStorage(0), haarScale, minNeighbors, haarFlags, minTargetSize )

		return suspects

	
			
if __name__ == "__main__":

	"""
	SAMPLE SCRIPT

	"""
	scan = Scan()
	scan.startCapture("",capdevice)
	scan.startWindow()

	tracking = Tracking()

	while True:
		img = cv.QueryFrame( scan.capture )			

		cr = 0.50		# compression rate			
		icr = 1.0/cr

		grayimg = cv.CreateImage( (img.width, img.height), 8, 1 )
		comprimg = cv.CreateImage( (cv.Round(img.width*cr), cv.Round(img.height*cr)), 8, 1)

		# covert image to gray
		cv.CvtColor( img, grayimg, cv.CV_BGR2GRAY )

		# scale input image
		cv.Resize( grayimg, comprimg, cv.CV_INTER_LINEAR )

		# equalize histogram
		cv.EqualizeHist( comprimg, comprimg )

		suspects = scan.haarScan(comprimg)
		
		store = False
		for suspect in suspects:
			if tracking.query(suspect) == "":
				store = True
		tracking.fade_all()
		print "Number of targets: " + str(len(tracking.foci))	
		for target in tracking.foci:
			score = target.get_score()/100.0
			color = (min(30,30*score),min(255,255*score),min(30,30*score))
			scan.write(img,target.get_pos() ,target.id(),color)

		cv.ShowImage(scan.windowname,img)

		if store:
			if not os.path.exists("./snapshots"):
				os.mkdir("snapshots")
			if not os.path.exists("./snapshots/"+time.strftime('%d-%b-%Y')):
				os.mkdir("./snapshots/"+time.strftime('%d-%b-%Y'))
				
			cv.SaveImage("./snapshots/"+time.strftime('%d-%b-%Y')+"/"+time.strftime('%H:%M:%S')+".jpg",img)

		
		key = cv.WaitKey(10)
		
		if key == 113:
			scan.killWindow()
			break
		else:
			if key != -1:
				print key

