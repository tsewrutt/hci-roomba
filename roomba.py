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
	ROGUE = 3


class Roomba(object):
	"""
	Class that represents the Roomba.
	"""
	global usersDoc_ref
	global movesDoc_ref
	global tasksDoc_ref
	global tasksCounter

	# Use google login
	cred = credentials.Certificate('hri-roomba-data-83bcb0b681a0.json')
	app = firebase_admin.initialize_app(cred)
	db = firestore.client()
	tasksDoc_ref = db.collection('tasks').stream()
	# controlsDirection_ref = db.collection('movements').document('direction')
	# isremoteControlled = controlsDirection_ref.get().to_dict()["IsRemoteControlled"]
	usersDoc_ref = db.collection('users').stream()


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
		self.make_songs()
	
	def make_songs(self):
		#array takes the sound frequency 
		i = [72, 32, 71, 16, 69, 16, 74, 32, 72, 16, 71, 32, 71, 16, 69, 16, 67, 16, 71, 16, 71, 32]
		self.create.song(Songs.NEUTRAL, i)

		j = [52, 64, 45, 32, 41, 16, 52, 32, 45, 32, 41, 32, 52, 32, 45, 16, 41, 16]
		self.create.song(Songs.NEUROTIC, j)

		k = [77, 16, 77, 16, 77, 16]
		self.create.song(Songs.ANXIOUS, k)

		l = [77,20,50,40,20,30,40,50,77]
		self.create.song(Songs.ROGUE, l)

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
		self.create.seek_dock()
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

		turn_time = 0.1
		
		timeout = time.monotonic() + duration * 60
		turn_timeout = 0

		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True

		self.create.leds(6, 0, 255)

		s_duration = self.create.play_song(Songs.NEUTRAL)
		time.sleep(s_duration)

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
					collision = Directions.FORWARD
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left!")
					is_colliding = True
					collision = Directions.LEFT
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right!")
					is_colliding = True
					collision = Directions.RIGHT

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				self.create.drive_stop()

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

		s_duration = self.create.play_song(Songs.NEUTRAL)
		time.sleep(s_duration)

		print("Done cleaning!")
		return time.monotonic() >= timeout
	
	def clean_neurotic(self, vel: int = 75, duration: int = 1):
		"""
		Start a neurotic cleaning cycle.

		Args:
			bot: Create class controlling Roomba.
			vel: Roomba movement speed.
			duration: The length of the cleaning cycle (minutes).

		Returns:
			The time remaining in the cleaning cycle. 0 if cycle completed successfully.
		"""
		print("Start neurotic cleaning.")

		turn_time = 0.15

		timeout = time.monotonic() + duration * 60
		turn_timeout = 0
		random_timeout = 0.3 # Roomba randomly changes direction

		movement = self.directions[Directions.FORWARD] * vel
		is_cleaning = True

		self.create.leds(8, 255, 128)

		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

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
					collision = Directions.FORWARD
				elif sensors.bumps_wheeldrops.bump_left == True:
					print("Bump Left.")
					is_colliding = True
					collision = Directions.LEFT
				elif sensors.bumps_wheeldrops.bump_right == True:
					print("Bump Right.")
					is_colliding = True
					collision = Directions.RIGHT

				if self.power_button == ButtonState.JUST_PRESSED:
					is_cleaning = False
				
				if time.monotonic() >= timeout:
					is_cleaning = False

			if is_colliding:
				self.create.motors_stop()
				self.create.drive_stop()
				
				s_duration = self.create.play_song(Songs.ANXIOUS)
				time.sleep(s_duration)

				print("Changing directions.") #when changing the directions the vel is constant which means roomba hits the wall with full speed, we may have to decrease the speed on that when sensor detects about to collide to wall
				movement = self.directions[Directions.BACK] * vel
				self.create.drive_direct(int(movement[0]), int(movement[1]))
				time.sleep(0.4)

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

		#self.create.motors_stop()
		self.create.drive_stop()

		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

		print("Done neurotic cleaning.")
		return time.monotonic() >= timeout
	
	def playAnxious(self):
		s_duration = self.create.play_song(Songs.ANXIOUS)
		time.sleep(s_duration)

	def playHappy(self):
		s_duration = self.create.play_song(Songs.NEUTRAL)
		time.sleep(s_duration)


	def updateSound(self):
		self.direction_data.update({'sound':""})

	def clearTask(self):
		self.direction_data.update({'task':'0'})

	def remoteMovement(self, vel: int = 200):
		self.create.leds(6, 127, 255)
		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

        # docDirection_ref.on_snapshot(on_snapshot)
        # self.direction_data = docDirection_ref
        # lets user know it is remote
		# isRemote = self.direction_data.get().to_dict()["IsRemoteControlled"]
		# direction = self.direction_data.get().to_dict()["direction"]
		# stop = self.direction_data.get().to_dict()["stop"]
		# sound = self.direction_data.get().to_dict()["sound"]
		# task = self.direction_data.get().to_dict()["task"]

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
					self.clean(duration = 1)
					self.clearTask()
				elif task == 2:
					self.clean(duration = 1)
					self.clearTask()
				elif task == 3:
					self.clean_neurotic(duration = 1)
					self.clearTask()
			else:
				# this could be roomba.drive...
				print("stop is true, so stop drive")
				self.create.drive_stop()
				
			if sound == 'anxious':
				self.playAnxious()
				self.updateSound()
			elif sound == 'happy':
				self.playHappy()
				self.updateSound()
				print("Happy")
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