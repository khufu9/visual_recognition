from numpy import *
#import scipy.linalg
import cv
import os
import re
import sys

""" A class for recognizing faces in portain images using eigenfaces.

An image is represented as a 1D column vector where the rows are stored 
consequently, having D = w x h number of elements. After having loaded 
a set of training images the average face is constructed by taking the 
row-wise average of all training images. This vector is called Xi. Xi, 
is the origin in the basis of linearly independent eigen vectors that 
is computed using PCA on the correlated training images A^T*A. 

Note that it is required that eigen vectors corresponding to a nonzero 
eigen value is removed from the basis.

An image can be found in the eigen space by first computing its eigen face:
	
	Eigen face = U^T*(Face - Average face)

Where U is the eigen space.

The distance metric implemented currently is the squared L2-distance. 
In the future, the error metric will use Mahalanobis distance.

This class can inherently load all file formats supported by openCVs 
loadImage method.

If you get an error looking for files in certain folders you have to 
change the paths manually below.
"""

class Recon:

	"""
	DESCRIPTION:
	Constructor
	
	PARAMETERS:
	path - 	a string containing the relative or absolute path to the library
			images.
	"""
	def __init__(self,path="./faces/"):
		self.nLambda = 0 				# Number of significant eigen vectors
		self.gammas = array([],ndmin=2)	# stored faces - average face
		self.imagedata = []
		self.Xi  = array([])			# average face
		self.U  = array([])				# face space of nLambda eigenvectors
		self.__path = path
		self.img_cols = 0				# width of a training image.
		self.img_rows = 0				# height of a training image.
		self.__sb = dict()				# score board
		self.matcher = re.compile(".jpg|.jpeg|.jpe|.pgm|.ppm|.pbm|.png|.tiff|.tif")
		# preparing data is considered a part of the constructor
		self.loadFaces()
		if self.gammas.shape[0] > 2:
			self.computeFaceSpace()

	def computeFaceSpace(self):
		"""		
		DESCRIPTION:
		Perform PCA to find the principal components belonging to the significant 
		eigen vectors (lambda_n > 0)
		"""
		dims = self.gammas.shape

		print dims

		self.Xi = array([mean(self.gammas,axis=1),]).T
	
		A = subtract(self.gammas,self.Xi)
		#[D,V] = scipy.linalg.eig( dot(A.T,A) )
		[D,V] = linalg.eig( dot(A.T,A) )
		[D,V] =	self.__sortByEigenValue(D,V)	
		D = sqrt(1.0/D)
		D = diag(D)	
		VDsqi = dot(V,D)
		self.U = dot(A,VDsqi)
		dims = self.U.shape
		if dims[1] < 1:
			print >> sys.stderr,"  Error: all eigenvalues are nonzero"
			self.nLambda = 0
		else:
			self.nLambda = dims[1]	

	def formattedPrint(self):
		for (name,val) in self.__sb.iteritems():
			print name+"\t"+str(val)
		
	
	def getScoreboard(self):
		return self.__sb	

	def get_num_faces(self):
		return self.gammas.shape[-1]
	
	def loadFaces(self):
		"""DESCRIPTION: 
		Load compatible images from the directory specified by attribute 'path'. 
		The default path is './faces/'.
		"""
		print "Loading targets from dir: " + self.__path
		# get only the file names of actual images
		flist= os.listdir( self.__path )	
		if len(flist) < 3:
			print "Error:  Library must consist of more than two images. No targets where loaded"
			return
		imlist = []
		for elem in flist:
			if self.matcher.search(elem.lower()) != None:
				imlist.append(elem)
				print self.__path + elem
		i = 0
		for imfile in imlist:
			# convert the picture to a numpy arr2D
			mat = cv.LoadImageM( self.__path + imfile, cv.CV_LOAD_IMAGE_GRAYSCALE) # supports png, jpg...
			self.__storeFace(mat)
			self.imagedata.append(imfile)
			i = i + 1

	def lookup(self, arr2D):
		"""
		DESCRIPTION:
		Compute the metric distance between the closest face class and the 
		matrix representation of an image. Lookup images are resized to fit 
		the eigen face basis before computing the distances. The distance metric 
		is the Mahalanobis distance.
		
		PARAMETERS:
		arr2D 	- a matrix representation of a portrait
		"""
		# For now, select all eigenfaces as a basis
		Uhat = self.U	
		if arr2D.rows != self.img_rows and arr2D.cols != self.img_cols:
			rimg = cv.CreateImage( (self.img_rows, self.img_cols), 8, 1 )
			cv.Resize( arr2D, rimg, cv.CV_INTER_LINEAR )
			arr2D = array(rimg) 
		gamma = reshape(array(arr2D),(self.img_rows*self.img_cols,1))
		phi   = subtract(gamma, self.Xi)
		eigface = dot( Uhat.T, phi) # project onto face space
		
		phi = subtract(self.gammas,self.Xi)
		omegak = dot(Uhat.T,phi)
		distvec = abs(sum(square(subtract(eigface,omegak))/square(std(subtract(eigface,omegak))),axis=0))
		dims = self.gammas.shape

		self.__sb = dict( zip(self.imagedata, distvec) )

		target = self.imagedata[list(distvec).index(min(distvec))]
		
		return target



	def resetAll(self):
		self.nLambda = 0 				# Number of significant eigen vectors
		self.gammas = array([],ndmin=2)	# stored faces - average face
		self.imagedata = []
		self.Xi  = array([])			# average face
		self.U  = array([])				# face space of nLambda eigenvectors
		self.img_cols = 0				# width of a training image.
		self.img_rows = 0				# height of a training image.
		self.__sb = dict()				# score board
		


	def __storeFace(self,arr2D):
		"""	DESCRIPTION: 
		Store a 2D matrix representing an image as a face class
	
		PARAMETERS:
		arr2D 	- a matrix representation of a portrait image
		"""
		if self.img_rows < 1 and self.img_cols < 1:
			# Require all subsequently loaded images to have the same size
			self.img_rows = arr2D.rows
			self.img_cols = arr2D.cols

		elif self.img_rows != arr2D.rows or self.img_cols != arr2D.cols:
			# This means that the loaded training image is another size
			rimg = cv.CreateImage( (self.img_rows, self.img_cols), 8, 1 )
			cv.Resize( arr2D, rimg, cv.CV_INTER_LINEAR )
			arr2D = rimg

		print asarray(arr2D).shape
		arr1D = reshape(asarray(arr2D[:,:]),(self.img_rows*self.img_cols,1))
		
		if len(self.gammas) == 1:
			self.gammas = arr1D
		else:
			self.gammas = hstack((self.gammas,arr1D))










	def __sortByEigenValue(self,D,V):
		"""
		DESCRIPTION:	
		Sort the vector of scalars D in descending order and swaps the columns 
		of input matrix V accordin to the sorted vector.
	
		PARAMETERS:
		D 	- a vector of eigenvalues
		V 	- the corresponding matrix of eigen vectors
		"""
		ind = D.argsort()[::-1]
		[D,V] = map(array,zip(*filter(lambda x: x[0]>0.0,zip(real(D[ind]),V[:,ind].T))))
		return [D,V.T]
	





	"""
	DESCRIPTION:
	Prints a projected image as an JPG-image.
	
	PARAMETERS:
	proj 	- any image represented as a 1D vector
	"""
	def genProjFace(self,proj):
		cv.SaveImage("projectedface.jpg",cv.fromarray(reshape(proj,(self.img_rows,self.img_cols))))
			
	# DESCRIPTION:
	# Prints the orogin (average face) as an image. Mainly used for debugging.
	def genAvgFace(self):
		cv.SaveImage("avgface.jpg",cv.fromarray(reshape(self.Xi,(self.img_rows,self.img_cols))))

	
