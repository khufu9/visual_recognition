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

* Real-time recognition
To start the example run:

	$: python2.7 realtime.py

Select a portrait to save by entering the numeric key 1-9 and press space. 
Enter the name and press enter. The portrait should now write out the file 
name you just entered. 

* Surveillance
To start the example run:

	$: python2.7 surveillance.py

The application records faces that can be recognized using Haar-detection. 
Faces are stored in folders by their data and the names are by the time. 
This application features improved tracking capabilites. 


