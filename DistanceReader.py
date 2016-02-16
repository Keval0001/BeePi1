import os
import threading
import time
import RPi.GPIO as GPIO
from FileOperations import FileOperations
from TimeUtils import TimeUtils

#utility method to get the current timestamp in a format that
#can be used as a valid filename in Windows and Linux/Unix
def getTimestamp():
	return time.strftime('%Y-%m-%d_%H-%M-%S')

#class that is used to record data at a specified interval
#tempReadFile is linux system file that is read to determine temperature, determined by parseConfig method
#saves data at tempSaveDirectory+tempSaveFilename
#interval is time in seconds between sampling data
class DistanceReader:
	def __init__(self, distReadFile, distSaveDirectory, distSaveFilename, interval, length):
		self.distanceReadFile = distReadFile
		self.distanceSaveFile = os.path.join(distSaveDirectory,distSaveFilename)
		self.sampleInterval = interval
		self.isRecording = False
		self.sampleLength = length
		self.recordingLoopActive = False
		self.threadsStarted = False
		self.nextTimer = None
		self.distLogger = FileOperations(distSaveDirectory, distSaveFilename)
	
	#starts recording distance at specified interval
	def startRecording(self):
		self.recordingLoopActive = True
		if(self.threadsStarted == False):
			threading.Timer(0, self.sampleDistanceWithInterval, ()).start()
			self.threadsStarted = True
	
	#requests recording thread to stop+pi-
	def stopRecording(self):
		self.recordingLoopActive = False
	
	#used to force the thread to stop recording if there was an error in recording data
	def resetIsRecording(self):
		self.isRecording = False
	
	#this method is called by timer threads to record data at the specified interval
	def sampleDistanceWithInterval(self):
		#launching next timer thread to record temp after specified interval
		self.nextTimer = threading.Timer(self.sampleInterval, self.sampleDistanceWithInterval, ())
		self.nextTimer.start()
		if(self.recordingLoopActive == True and self.storage.hasSpace()):
			self.isRecording = True
			#line below ensures that, even when there is an error recording distance, isRecording won't stay on
			#The pi has 10 seconds to record temperature
			threading.Timer(self.sampleLength + 15, self.resetIsRecording, ()).start()
			timestamp = getTimestamp()
			try:
				self.logger.log("[DistanceSensor] started recording distance")
				end_time = time.time() + self.sampleLength
				while time.time() < end_time:	
					distance = self.readDistance()
					timestamp = TimeUtils.getTimestamp()
					output = "%s %f\n" % (timestamp, distance)
					self.distLogger.appendToFile(output)
				self.logger.log("[DistacneReaader] recorded distance")
			except Exception as e:
				self.logger.logError("DistanceReader", "Error reading distance", e)
			self.isRecording = False
	
	#this method is to take input and output from the sensor and return the measured distance to measure_average
	def measure(self):
		GPIO.output(24, True)
		time.sleep(0.00001)
		GPIO.output(24, False)
		start = time.time()
		
		while GPIO.input(23)==0:
			start = time.time()

		while GPIO.input(23)==1:
			stop = time.time()

		elapsed = stop - start
		distance = (elapsed*34300)/2
		return distance

	#this method returns average of distance to readDistance (this method is for accuracy) 
	def measure_average(self):
		
		distance1 = self.measure()
		time.sleep(0.1)
		distance2 = self.measure()
		distance = distance1 + distance2	
		distance = distance/2
		return distance
	#this method is reading the distance
	def readDistance(self):
		with open(self.distanceReadFile, 'r') as distanceFile:
			while True:
				distance = self.measure_average()
				time.sleep(0.1)
				return distance
			GPIO.cleanup()

	#cancels any timers that are waiting to excecute. Used when quitting the program
	def quit(self):
		if self.nextTimer != None:
			self.nextTimer.cancel()
			
	def setLogger(self, logger):
		self.logger = logger
		
	def setStorage(self, storage):
		self.storage = storage
	
			
