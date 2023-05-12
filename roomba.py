from enum import Enum, IntEnum
from pycreate600 import Create

import numpy as np

import random
import requests
import sys
import time


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
	ANXIOUS = 2


class Roomba(object):
	"""
	Class that represents the Roomba.
	"""

	def __init__(self, port):
		"""
		Constructor.
		"""

		# login credentials
		self.username = "coneill"
		self.password = "password"

		self.directions = [np.array([1, 1]), np.array([-1, -1]), np.array([0, 1]), np.array([1, 0])]
		self.power_button = ButtonState.RELEASED

		self.create = Create(port=port)
		self.create.start()
		self.create.full()
		self.make_songs()
	
	def make_songs(self):
		i = [72, 32, 71, 16, 69, 16, 74, 32, 72, 16, 71, 32, 71, 16, 69, 16, 67, 16, 71, 16, 71, 32]
		self.create.song(Songs.NEUTRAL, i)

		j = [52, 64, 45, 32, 41, 16, 52, 32, 45, 32, 41, 32, 52, 32, 45, 16, 41, 16]
		self.create.song(Songs.NEUROTIC, j)

		k = [77, 16, 77, 16, 77, 16]
		self.create.song(Songs.ANXIOUS, k)

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
	
	def has_task(self):
		try:
			login_url = "https://robotportal.herokuapp.com/api/auth/login"
			info_url = "https://robotportal.herokuapp.com/api/users/info"
			tasks_url = "https://robotportal.herokuapp.com/api/users/{uid}/tasks"

			credentials = {
				"username": self.username,
				"password": self.password
			}

			auth_res = requests.post(login_url, json=credentials).json()
			token = "Bearer " + auth_res["token"]

			info_res = requests.get(info_url, headers={"Authorization": token}).json()
			uid = info_res["id"]

			tasks = requests.get(tasks_url.format(uid = uid), headers={"Authorization": token}).json()
			if any(i["complete"] == False and i["skipped"] == False for i in tasks):
				return True

			if tasks[len(tasks)-1]["skipped"] == True:
				return True
			return False
		except Exception:
			return False

	def post_task(self):
		try:
			login_url = "https://robotportal.herokuapp.com/api/auth/login"
			info_url = "https://robotportal.herokuapp.com/api/users/info"
			tasks_url = "https://robotportal.herokuapp.com/api/users/{uid}/tasks"

			credentials = {
				"username": self.username,
				"password": self.password
			}

			auth_res = requests.post(login_url, json=credentials).json()
			token = "Bearer " + auth_res["token"]

			info_res = requests.get(info_url, headers={"Authorization": token}).json()
			uid = info_res["id"]

			tasks_res = requests.get(tasks_url.format(uid = uid), headers={"Authorization": token}).json()
			tid = len(tasks_res) + 1

			if tid >= 3:
				return
			
			user_task = {
				"userId": uid,
				"taskId": tid
			}
			requests.post(tasks_url.format(uid = uid), json=user_task, headers={"Authorization": token}).json()
			return True
		except Exception:
			return False
	
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

		self.create.motors_stop()
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

				print("Changing directions.")
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

		self.create.motors_stop()
		self.create.drive_stop()

		s_duration = self.create.play_song(Songs.NEUROTIC)
		time.sleep(s_duration)

		print("Done neurotic cleaning.")
		return time.monotonic() >= timeout


if __name__ == "__main__":
	port = "/dev/ttyUSB0"

	roomba = Roomba(port)

	try:
		while True:
			roomba.update_power_button()
			if roomba.power_button == ButtonState.JUST_PRESSED:
				if roomba.has_task():
					roomba.clean_neurotic(duration=5)
				else:
					if roomba.clean(duration=3):
						while roomba.post_task() == False:
							time.sleep(1)
						roomba.clean_neurotic(duration=2)
			time.sleep(0.01)
	except KeyboardInterrupt:
		print("Exiting...")

	sys.exit()