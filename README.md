###############################################################################
#                                                                             #
#                             VISUAL RECOGNITION                         	  #
#                                                                             #
#      Computer visual recognition library using OpenCV implemented in python #
###############################################################################

About
-----

This library implements computer vision by the method of Eigenfaces. Detection 
is performed using the Haar algorithm. 

Dependecies
-----------

* OpenCV (tested 2.4.2)
* Numpy (tested 1.6.2)
* Python 2.X


Examples
--------

An example application is provided which demo the application in real-time. 
To start the example run:

	$: python2.7 realtime.py

Select a portrait to save by entering the numeric key 1-9 and press space. 
Enter the name and press enter. The portrait should now write out the file 
name you just entered. 

Errors
------

No subdirectory "faces":

	$: ... No such file or directory: './faces/'

Simply create the directory.


