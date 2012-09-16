__version__ = 0.1

import os
import cv
import numpy
import math
import recon

capdevice =0 # 0 for integrated cam 1 for usb-cam

class Scan:

	def __init__(self,wn="Camera view"):
		self.windowname = wn
		self.capture = None
		self.sounds = dict()
		self.targets = []
		self.currentface = None
		self.selected = None
		self.selectedimg = None

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

		faceCascade = cv.Load("./haarcascade_frontalface_alt.xml")

		haarScale = 1.2
		minNeighbors = 2
		haarFlags = 0
		minTargetSize = (20,20)
		
		suspects = cv.HaarDetectObjects( comprimg, faceCascade, cv.CreateMemStorage(0), haarScale, minNeighbors, haarFlags, minTargetSize )

		return suspects

	
			
if __name__ == "__main__":

	"""
	SAMPLE SCRIPT

	"""
	scan = Scan()
	scan.startCapture("",capdevice)
	scan.startWindow()

	lib = recon.Recon()

	while True:
		img = cv.QueryFrame( scan.capture )			

		cr = 0.40		# compression rate			
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

		port = cv.CreateImage( (134,179),8,3 )
		offset = 0

		num = 1
		if suspects:
			
			for ((x,y,w,h), n) in suspects:
				top_left = (int(x*icr)+int(5*icr), int(y*icr)+int(10*icr))
				bottom_right = (int((x+w) * icr)-int(5*icr), int((y+h)*icr)-int(0*icr))
				x = int(x*icr)+15
				y = int(y*icr)+10
				w = int(w*icr)-15
				h = int(h*icr)-10

				cv.SetImageROI( img, (x,y,w,h) )
				face = cv.CreateImage((w,h),8,3)
				gport = cv.CreateImage((134,179),8,1)
				cv.Copy(img,face)
				cv.ResetImageROI(img)
				cv.Resize(face,port,cv.CV_INTER_LINEAR)
				cv.CvtColor(port,gport,cv.CV_BGR2GRAY)
				cv.EqualizeHist(gport,gport)
				cv.SetImageROI( img, (10+offset,img.height-189,134,179) )
				cv.Copy(port,img)
				scan.write(img,(5,160),lib.lookup(cv.GetMat(gport)),(255,255,255))
				if num == scan.selected:
					cv.Rectangle(img, (0,0),(134-2,179-2), cv.RGB(255,0,0),2,8,0)
					scan.selectedimg = gport


				scan.currentface = cv.CloneImage(gport)

				cv.ResetImageROI(img)
				offset += 144

				num = num + 1

		cv.ShowImage(scan.windowname,img)
		
		for (t,n1) in scan.targets:
			for s in suspects:
				sc = s[0]
				sx = sc[0]; sy = sc[1]
				tx = t[0]; ty = t[1]
				if abs(tx-sx)+abs(ty-sy) < 100.0:
					suspects.remove(s)
					break
		# add remaining suspects
		for s in suspects:
			print ">> New target found"
			scan.targets.append(s)
		
		key = cv.WaitKey(10)
		
		if key == 113:
			scan.killWindow()
			break
		if key == 32:
			name = raw_input("   Enter name:")
			cv.SaveImage("./faces/"+name+".jpg", scan.selectedimg)
			lib.resetAll()
			lib.loadFaces()
			lib.computeFaceSpace()
		if key-48 in xrange(1,5):
			numf = key-48
			scan.selected = numf
			print "   Selected target",num
		elif key != -1:
			print key

