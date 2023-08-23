from enum import Enum, IntEnum
import time
from pycreate600 import Create
from firebase_admin import db
import numpy as np

import random
import requests
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class ButtonState(Enum):
	PRESSED = 0,
	JUST_PRESSED = 1,
	RELEASED = 2


class Directions(IntEnum):
	FORWARD = 0,
	BACK = 1,
	LEFT = 2,
	RIGHT = 3


class Songs(IntEnum):
	NEUTRAL = 0,
	NEUROTIC = 1,
	ANXIOUS = 2,
	OTHERS = 3


class Roomba(object):
	"""
	Class that represents the Roomba.
	"""
	global usersDoc_ref
	global movesDoc_ref
	global tasksDoc_ref
	global tasksCounter
	global totalCollisions

	# Use google login
	cred = credentials.Certificate('hri-roomba-data-f99a14d0631b.json')
	app = firebase_admin.initialize_app(cred)
	db = firestore.client()
	tasksDoc_ref = db.collection('tasks').stream()
	# controlsDirection_ref = db.collection('movements').document('direction')
	# isremoteControlled = controlsDirection_ref.get().to_dict()["IsRemoteControlled"]
	usersDoc_ref = db.collection('users').stream()
	totalCollisions = 0

	def __init__(self, port):
		"""
		Constructor.
		"""
		db = firestore.client()
		docDirection_ref = db.collection('movements').document('direction')
		docDirection_ref.on_snapshot(on_snapshot)
		self.direction_data = docDirection_ref
		


		self.directions = [np.array([1, 1]), np.array([-1, -1]), np.array([0, 1]), np.array([1, 0])]
		self.power_button = ButtonState.RELEASED

		self.create = Create(port=port)
		self.create.start()
		self.create.full()
		#self.make_songs()
	
	# def make_songs(self):
	# 	#array takesmidi notes followed by duration of the note
		

	def update_power_button(self):
		"""
		Updates state of Roomba power button.
		"""
		pressed = self.create.sensors().buttons.clean
		if pressed and (self.power_button == ButtonState.RELEASED):
			self.power_button = ButtonState.JUST_PRESSED
		elif pressed:
			self.power_button = ButtonState.PRESSED
		else:
			self.power_button = ButtonState.RELEASED
	
	#This func will be called in the main loop until all task is completed
	def has_task(self):
		try:
			tasksCounter = 0
			for doc in tasksDoc_ref:
				if(doc.to_dict()["status"] == "incomplete"):
					tasksCounter = tasksCounter + 1

			if(tasksCounter > 0):
				return True
			else:
				return False
	
		except Exception:
			return False
		

	def dock(self):
		"""
		Call onto the seek_dock() function which directs Roomba to drive onto the dock
		the next time it encounters the docking beams
		"""
		#stop = False
# 			stop = self.direction_data.get().to_dict()["stop"]
		self.create.seek_dock()
# 			self.create.drive_stop()
	
	#completed, failed , pending, incomplete
	def clean(self, vel: int = 250, duration: int = 1):
		"""
		Start a neutral cleaning cycle.

		Args:
			bot: Create class controlling Roomba.
			vel: Roomba movement speed.
			duration: The length of the cleaning cycle (minutes).

		Returns:
			The time remaining in the cleaning cycle. 0 if cycle completed successfully.
		"""
		print("Start cleaning!")
		numOfCollisions = 0
		turn_time = 0.1
		
		timeout = time.monotonic() + duration * 60
		turn_timeout = 0

		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True

		self.create.leds(6, 0, 255)

		self.playNeutral()
		#s_duration = self.create.play_song(Songs.NEUTRAL)
		#time.sleep(s_duration)

		self.create.motors(13)
		
		#we can add the stop check here, but look at read write stats first before doing that
		while is_cleaning:
			is_colliding = False
			collision = None

			self.create.motors(13)
			while is_cleaning and not is_colliding:
				self.update_power_button()
				if turn_timeout <= 0:
					movement = self.directions[Directions.FORWARD] * vel
				else:
					turn_timeout -= 0.001
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.001)

				sensors = self.create.sensors()
				if sensors.bumps_wheeldrops.bump_left == True and sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Middle!")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.FORWARD
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left!")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.LEFT
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right!")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.RIGHT

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				self.create.drive_stop()
				self.create.motors_stop()
				
				if numOfCollisions <= 10:
					self.fastenedChimes(5)
				
				print("Changing directions!")
				movement = self.directions[Directions.BACK] * (vel / 2)
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.35)

				if collision == Directions.FORWARD:
					print("Turning Around!")
					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * (vel / 2) if i == 0 else self.directions[Directions.RIGHT] * (vel / 2)
					turn_timeout = turn_time
				elif collision == Directions.LEFT:
					print("Turning Right!")
					movement = self.directions[Directions.RIGHT] * (vel / 2)
					turn_timeout = turn_time
				elif collision == Directions.RIGHT:
					print("Turning Left!")
					movement = self.directions[Directions.LEFT] * (vel / 2)
					turn_timeout = turn_time

		#we dont stop motors when done cleaning now, that'll be when we call stop
		#self.create.motors_stop()
		self.create.drive_stop()

		self.playNeutral()

		print("Done cleaning!")
		return time.monotonic() >= timeout
	
	def clean_neurotic(self, vel: int = 200, duration: int = 1):
		"""
		Start a neurotic cleaning cyce.

		Args:
			bot: Create class controlling Roomba.
			vel: Roomba movement speed.
			duration: The length of the cleaning cycle (minutes).

		Returns:
			The time remaining in the cleaning cycle. 0 if cycle completed successfully.
		"""
		print("Start neurotic cleaning.")

		turn_time = 0.1 #changed the turn time -----> was doing too much of a loop when collision happens
		numOfCollisions = 0
		timeout = time.monotonic() + duration * 60
		turn_timeout = 0
		random_timeout = 0.3 # Roomba randomly changes direction

		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True

		self.create.leds(8, 255, 128)

		self.playNeurotic()

		self.create.motors(13)

		while is_cleaning:
			is_colliding = False
			collision = None

			self.create.motors(13)
			while is_cleaning and not is_colliding:
				self.update_power_button()
				self.create.leds(8, 255, 128)
				if turn_timeout < 0:
					movement = self.directions[Directions.FORWARD] * vel
					random_timeout = random.randint(5, 15) / 10
					turn_timeout = 0
				elif turn_timeout > 0:
					turn_timeout -= 0.001
				
				if turn_timeout == 0 and random_timeout < 0:
					print("Randomly switching directions.")
					self.create.motors_stop()
					self.create.drive_stop()
					
					s_duration = self.create.play_song(Songs.ANXIOUS)
					time.sleep(s_duration)

					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * vel if i == 0 else self.directions[Directions.RIGHT] * vel
					
					turn_timeout = turn_time * 2
					random_timeout = random.randint(4, 10) / 10

					s_duration = self.create.play_song(Songs.ANXIOUS)
					time.sleep(s_duration)

					self.create.motors(13)
				elif turn_timeout == 0 and random_timeout > 0:
					random_timeout -= 0.001

				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.001)

				sensors = self.create.sensors()
				if sensors.bumps_wheeldrops.bump_left == True and sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Middle.")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.FORWARD
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left.")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.LEFT
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right.")
					is_colliding = True
					numOfCollisions = numOfCollisions + 1
					collision = Directions.RIGHT

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				self.create.motors_stop()
				self.create.drive_stop()
				
				if numOfCollisions <= 10:
					self.playDoubleBeep()

				print("Changing directions.")
				movement = self.directions[Directions.BACK] * vel
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.35)

				if collision == Directions.FORWARD:
					print("Turning Around.")
					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * vel if i == 0 else self.directions[Directions.RIGHT] * vel
					turn_timeout = turn_time
				elif collision == Directions.LEFT:
					print("Turning Right.")
					movement = self.directions[Directions.RIGHT] * vel
					turn_timeout = turn_time
				elif collision == Directions.RIGHT:
					print("Turning Left.")
					movement = self.directions[Directions.LEFT] * vel
					turn_timeout = turn_time

		self.create.drive_stop()

		self.playNeurotic()

		print("Done neurotic cleaning.")
		return time.monotonic() >= timeout
	
	def clean_neurotic_escalating(self, vel: int = 200, duration: int = 1):
		
		print("Start neurotic cleaning.")
		numOfCollisions = 0
		turn_time = 0.1

		timeout = time.monotonic() + duration * 60
		turn_timeout = 0
		random_timeout = 0.3 # Roomba randomly changes direction
		stop = self.direction_data.get().to_dict()["stop"]
		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True

		self.create.leds(8, 255, 128)

		self.playNeurotic()

		self.create.motors(13)

		while is_cleaning and not stop:
			is_colliding = False
			collision = None
			stop = self.direction_data.get().to_dict()["stop"]

			self.create.motors(13)
			while is_cleaning and not is_colliding:
				self.update_power_button()
				self.create.leds(8, 255, 128)
				if turn_timeout < 0:
					movement = self.directions[Directions.FORWARD] * vel
					random_timeout = random.randint(5, 15) / 10
					turn_timeout = 0
				elif turn_timeout > 0:
					turn_timeout -= 0.001
				
				if turn_timeout == 0 and random_timeout < 0:
					print("Randomly switching directions.")
					self.create.motors_stop()
					self.create.drive_stop()
					
					#playing one beep on rando
					self.playDoubleBeep()

					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * vel if i == 0 else self.directions[Directions.RIGHT] * vel
					
					turn_timeout = turn_time * 2
					random_timeout = random.randint(4, 10) / 10

					
					#self.playBeep()

					self.create.motors(13)
				elif turn_timeout == 0 and random_timeout > 0:
					random_timeout -= 0.001

				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.001)

				sensors = self.create.sensors()
				if sensors.bumps_wheeldrops.bump_left == True and sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Middle.")
					is_colliding = True
					collision = Directions.FORWARD
					numOfCollisions = numOfCollisions + 1
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left.")
					is_colliding = True
					collision = Directions.LEFT
					numOfCollisions = numOfCollisions + 1
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right.")
					is_colliding = True
					collision = Directions.RIGHT
					numOfCollisions = numOfCollisions + 1

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				#stop motor and drive
				self.create.motors_stop()
				self.create.drive_stop()
				
				if numOfCollisions == 1:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 2:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 3:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 4:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 5:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 6:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 7:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 8:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 9:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 10:
					self. prolongatedBeeps(numOfCollisions)
					time.sleep(0.1)	
					#is_cleaning = False
					# After 8th collision we continue task until time is done
				#if numOfCollisions == 8:
				#	totalCollisions = totalCollisions + numOfCollisions
				#	numOfCollisions = 0 #resets num count and do it from the start again
					#is_cleaning = False
				#wait for user reaction in 5 seconds 
				time.sleep(1)


				print("Changing directions.")
				movement = self.directions[Directions.BACK] * vel
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.35)

				if collision == Directions.FORWARD:
					print("Turning Around.")
					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * vel if i == 0 else self.directions[Directions.RIGHT] * vel
					turn_timeout = turn_time
				elif collision == Directions.LEFT:
					print("Turning Right.")
					movement = self.directions[Directions.RIGHT] * vel
					turn_timeout = turn_time
				elif collision == Directions.RIGHT:
					print("Turning Left.")
					movement = self.directions[Directions.LEFT] * vel
					turn_timeout = turn_time
			#check if stop
			stop = self.direction_data.get().to_dict()["stop"]
			
		self.create.drive_stop()

		self.playNeurotic()

		print("Done neurotic cleaning.")
		return time.monotonic() >= timeout
		
		#new task 4 - non neurotic escalating
	def clean_nonneurotic_escalating(self, vel: int = 200, duration: int = 1):
		"""
		Start a clean non neutral cleaning cycle.

		Args:
			bot: Create class controlling Roomba.
			vel: Roomba movement speed.
			duration: The length of the cleaning cycle (minutes).

		Returns:
			The time remaining in the cleaning cycle. 0 if cycle completed successfully.
		"""
		print("Start cleaning!")

		turn_time = 0.1
		
		timeout = time.monotonic() + duration * 60
		turn_timeout = 0
		stop = self.direction_data.get().to_dict()["stop"]

		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True
		numOfCollisions = 0
		self.create.leds(6, 0, 255)

		self.playNeutral()

		self.create.motors(13)
		
		# we can add the stop check here, but look at read write stats first before doing that
		while is_cleaning and not stop:
			is_colliding = False
			collision = None
			stop = self.direction_data.get().to_dict()["stop"]

			self.create.motors(13)
			while is_cleaning and not is_colliding:
				self.update_power_button()
				if turn_timeout <= 0:
					movement = self.directions[Directions.FORWARD] * vel
				else:
					turn_timeout -= 0.001
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.001)

				sensors = self.create.sensors()
				if sensors.bumps_wheeldrops.bump_left == True and sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Middle!")
					is_colliding = True
					collision = Directions.FORWARD
					numOfCollisions = numOfCollisions + 1
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left!")
					is_colliding = True
					collision = Directions.LEFT
					numOfCollisions = numOfCollisions + 1
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right!")
					is_colliding = True
					collision = Directions.RIGHT
					numOfCollisions = numOfCollisions + 1

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				self.create.motors_stop()
				self.create.drive_stop()
				
				if numOfCollisions == 1:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 2:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 3:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 4:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 5:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 6:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 7:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)
				elif numOfCollisions == 8:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 9:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)	
				elif numOfCollisions == 10:
					self.fastenedChimes(numOfCollisions)
					time.sleep(0.1)	
					#is_cleaning = False
					#After 8th collision we continue task until time is done

				print("Changing directions!")
				movement = self.directions[Directions.BACK] * (vel / 2)
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.35)
				# every time there's a collision play the happy sound! or play it randomly
				if collision == Directions.FORWARD:
					print("Turning Around!")
					i = random.randint(0, 1)
					movement = self.directions[Directions.LEFT] * (vel / 2) if i == 0 else self.directions[Directions.RIGHT] * (vel / 2)
					turn_timeout = turn_time
				elif collision == Directions.LEFT:
					print("Turning Right!")
					movement = self.directions[Directions.RIGHT] * (vel / 2)
					turn_timeout = turn_time
				elif collision == Directions.RIGHT:
					print("Turning Left!")
					movement = self.directions[Directions.LEFT] * (vel / 2)
					turn_timeout = turn_time

		# we don't stop motors when done cleaning now, that'll be when we call stop
		# self.create.motors_stop()
		self.create.drive_stop()

		self.playNeutral()

		print("Done cleaning!")
		return time.monotonic() >= timeout

	
	def playNeurotic(self):
		self.create.clear_song_memory()
		s = [52, 64, 45, 32, 41, 16, 52, 32, 45, 32, 41, 32, 52, 32, 45, 16, 41, 16]
		self.create.song(Songs.NEUROTIC, s)
		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

	#plays a beep sound for num 4
	def playBeep(self):
		self.create.clear_song_memory()
		#definition of the new chime now
		s = [77,20]
		self.create.song(Songs.OTHERS, s)
		s_duration = self.create.play_song(Songs.OTHERS)
		time.sleep(s_duration)
        
        #triple beeps
	def playAnxious(self):
		self.create.clear_song_memory()
		s = [77, 20, 77, 20, 77, 20]
		self.create.song(Songs.ANXIOUS, s)
		s_duration = self.create.play_song(Songs.ANXIOUS)
		time.sleep(s_duration)

	def fastenedChimes(self, collisions):
		self.create.clear_song_memory()
		#test if we can add a gap b/w 84 and 82, 
		s = [84, 20, 87, 20, 89, 10, 90, 10, 89, 10, 87, 20, 84, 20, 82, 20, 79, 10, 78, 10, 79, 10, 82, 20, 84, 20]
		if collisions == 1:
			s = [84, 65, 87, 65, 89, 55, 90, 55, 89, 55, 87, 65, 84, 65, 82, 65, 79, 55, 78, 55, 79, 55, 82, 65, 84, 65]
		elif collisions == 2:
			s = [84, 60, 87, 60, 89, 50, 90, 50, 89, 50, 87, 60, 84, 60, 82, 60, 79, 50, 78, 50, 79, 50, 82, 60, 84, 60]
		elif collisions == 3:
			s = [84, 55, 87, 55, 89, 45, 90, 45, 89, 45, 87, 55, 84, 55, 82, 55, 79, 45, 78, 45, 79, 45, 82, 55, 84, 55]
		elif collisions == 4:
			s = [84, 50, 87, 50, 89, 40, 90, 40, 89, 40, 87, 50, 84, 50, 82, 50, 79, 40, 78, 40, 79, 40, 82, 50, 84, 50]
		elif collisions == 5:
			s = [84, 45, 87, 45, 89, 35, 90, 35, 89, 35, 87, 45, 84, 45, 82, 45, 79, 35, 78, 35, 79, 35, 82, 45, 84, 45]
		elif collisions == 6:
			s = [84, 40, 87, 40, 89, 30, 90, 30, 89, 30, 87, 40, 84, 40, 82, 40, 79, 30, 78, 30, 79, 30, 82, 40, 84, 40]
		elif collisions == 7:
			s = [84, 35, 87, 35, 89, 25, 90, 25, 89, 25, 87, 35, 84, 35, 82, 35, 79, 25, 78, 25, 79, 25, 82, 35, 84, 35]
		elif collisions == 8:
			s = [84, 30, 87, 30, 89, 20, 90, 20, 89, 20, 87, 30, 84, 30, 82, 30, 79, 20, 78, 20, 79, 20, 82, 30, 84, 30]
		elif collisions == 9:
			s = [84, 25, 87, 25, 89, 15, 90, 15, 89, 15, 87, 25, 84, 25, 82, 25, 79, 15, 78, 15, 79, 15, 82, 25, 84, 25]
		elif collisions == 10:
			s = [84, 20, 87, 20, 89, 10, 90, 10, 89, 10, 87, 20, 84, 20, 82, 20, 79, 10, 78, 10, 79, 10, 82, 20, 84, 20]
		self.create.song(Songs.OTHERS, s)
		s_duration = self.create.play_song(Songs.OTHERS)
		time.sleep(s_duration)

	def prolongatedBeeps(self, collisions):
		self.create.clear_song_memory()
		s = [77, 20, 77, 20, 77, 20]
		if collisions == 1:
			s = [77, 20, 77, 20, 77, 20]
		elif collisions == 2:
			s = [77, 40, 77, 40, 77, 40]
		elif collisions == 3:
			s = [77, 60, 77, 60, 77, 60]
		elif collisions == 4:
			s = [77, 80, 77, 80, 77, 80]
		elif collisions == 5:
			s = [77, 100, 77, 100, 77, 100]
		elif collisions == 6:
			s = [77, 120, 77, 120, 77, 120]
		elif collisions == 7:
			s = [77, 140, 77, 140, 77, 140]
		elif collisions == 8:
			s = [77, 160, 77, 160, 77, 160]
		elif collisions == 9:
			s = [77, 180, 77, 180, 77, 180]
		elif collisions == 10:
			s = [77, 200, 77, 200, 77, 200]
		self.create.song(Songs.ANXIOUS, s)
		s_duration = self.create.play_song(Songs.ANXIOUS)
		time.sleep(s_duration)

	def playNeutral(self):
		self.create.clear_song_memory()
		# this would be a different chime which is also the one we'll use for nne
		i = [72, 32, 71, 16, 69, 16, 74, 32, 72, 16, 71, 32, 71, 16, 69, 16, 67, 16, 71, 16, 71, 32]
		self.create.song(Songs.NEUTRAL, i)
		s_duration = self.create.play_song(Songs.NEUTRAL)
		time.sleep(s_duration)
		
	def playHappy(self):
		self.create.clear_song_memory()
		# this would be a different chime which is also the one we'll use for nne
		i = [84, 20, 87, 20, 89, 20, 90, 20, 89, 20, 87, 20, 84, 50, 82, 20, 85, 20, 84, 50]
		self.create.song(Songs.OTHERS, i)
		s_duration = self.create.play_song(Songs.OTHERS)
		time.sleep(s_duration)
		
	def playDoubleBeep(self):
		self.create.clear_song_memory()
		#definition of the new chime now
		m = [77,20,77,20]
		self.create.song(Songs.OTHERS, m)
		s_duration = self.create.play_song(Songs.OTHERS)
		time.sleep(s_duration)

	def updateSound(self):
		self.direction_data.update({'sound':""})

	def clearTask(self):
		self.direction_data.update({'task':'0'})

	def remoteMovement(self, vel: int = 200):
		self.create.leds(6, 127, 255)
		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

		#Have preset data
		isRemote = True
		direction = 1
		stop = False
		sound = ""
		task = 0
		
		self.create.motors(13)
    # starts off with forward
		print(self.direction_data.get().to_dict())
		movement = self.directions[Directions.FORWARD] * vel
		while isRemote:
			isRemote = self.direction_data.get().to_dict()["IsRemoteControlled"]
			stop = self.direction_data.get().to_dict()["stop"]
			sound = self.direction_data.get().to_dict()["sound"]
			if not stop:
				direction = self.direction_data.get().to_dict()["direction"]
				task = self.direction_data.get().to_dict()["task"]
				# drive direct moves roomba, if this is not present the roomba stay still
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.001)
				if direction == 0:
					movement = self.directions[Directions.FORWARD] * vel
					print("Forward")
				elif direction == 1:
					movement = self.directions[Directions.BACK] * vel
					print("back")
				elif direction == 2: #direction left right is reversed for control
					movement = self.directions[Directions.RIGHT] * vel
					print("right")
				elif direction == 3:
					print("left")
					movement = self.directions[Directions.LEFT] * vel
				
				if task == 1:
					self.clean(duration = 5)
					self.clearTask()
				elif task == 2:
					self.clean_neurotic(duration = 5)
					self.clearTask()
				elif task == 3:
					self.clean_neurotic_escalating(duration = 5)
					self.clearTask()
				elif task == 4:
					self.clean_nonneurotic_escalating(duration = 5)
					self.clearTask()
					

				#SOUND CHECK
				# if sound == 'beep':
				# 	self.playBeep()
				# 	self.updateSound()
				# elif sound == 'happy':
				# 	self.playHappy()
				# 	self.updateSound()

			else:
				# this could be roomba.drive...
				print("stop is true, so stop drive")
				self.create.drive_stop()
			
			#this is to be able to play the sound when roomba is idle
			if sound == 'anxious':
				self.playAnxious()
				self.updateSound()
			elif sound == 'happy':
				#This would play the happy sound which we need to make
				self.playHappy()
				self.updateSound()
			elif sound == 'beep':
				self.playBeep()
				self.updateSound()
			elif task == 'dock':
				self.dock()
				self.clearTask()
			
			#update sound to empty

		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)
		self.create.motors_stop()
		return
	
	#recursive func for real-time updates
def on_snapshot(doc_snap,changes,readtime):
	return




if __name__ == "__main__":
	port = "/dev/ttyUSB0"

	roomba = Roomba(port)

	try:
		dirDoc = roomba.direction_data.get().to_dict()
		isremoteControlled =dirDoc["IsRemoteControlled"]

		while True:
			roomba.update_power_button()
			if roomba.power_button == ButtonState.JUST_PRESSED:

				if roomba.has_task():
					# may have to check what task so we can decide on neurotic or non neurotic cleaning
					if isremoteControlled:
						# roomba.create.motors_stop()
						# roomba.create.drive_stop()
						# let control
						print("remote movement")
						roomba.remoteMovement()
					else:
						print("stop")
						# roomba.create.motors_stop()
						# roomba.create.drive_stop()
						# problem here, everytime switches to this one, it re runs the task
						# roomba.clean(duration=3)
						# normal clean
				else:
					print("Tasks Completed")


			time.sleep(0.01)
	except KeyboardInterrupt:
		print("Exiting...")

	sys.exit()