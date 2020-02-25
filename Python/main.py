import math
import time
import numpy as np

from scipy import interpolate

from utils import *


class Vector3:
    """
    Creates a Vector3 Object that can be used for any data which need 3 numbers.
    Create an Object by calling 'Vector3([x, y, z])' where x, y, z are your values.
    """

    def __init__(self, data):
        self.data = data

    def __add__(self, other):
        return Vector3([self.data[0] + other.data[0], self.data[1] + other.data[1], self.data[2] + other.data[2]])

    def __sub__(self, other):
        return Vector3([self.data[0] - other.data[0], self.data[1] - other.data[1], self.data[2] - other.data[2]])

    def __mul__(self, other):
        return Vector3([self.data[0] * other, self.data[1] * other, self.data[2] * other])

    def __truediv__(self, other):
        return Vector3([self.data[0] / other, self.data[1] / other, self.data[2] / other])

    def __abs__(self):
        return Vector3([abs(self.data[0]), abs(self.data[1]), abs(self.data[2])])

    def __eq__(self, other):
        return self.data[0] == other.data[0], self.data[1] == other.data[1], self.data[2] == other.data[2]

    def __gt__(self, other):
        return self.data[0] > other.data[0], self.data[1] > other.data[1], self.data[2] > other.data[2]

    def __lt__(self, other):
        return self.data[0] < other.data[0], self.data[1] < other.data[1], self.data[2] < other.data[2]

    def tolist(self):
        return [self.data[0], self.data[1], self.data[2]]

    def cap(self, low, high):
        return Vector3(max(min(self.data[0], high[0]), low[0]), max(min(self.data[0], high[0]), low[0]),
                       max(min(self.data[2], high[2]), low[2]))

    def magnitude(self):
        return math.sqrt((self.data[0] * self.data[0]) + (self.data[1] * self.data[1]) + (self.data[2] * self.data[2]))

    def normalize(self):
        mag = self.magnitude()
        if mag != 0:
            return Vector3([self.data[0] / mag, self.data[1] / mag, self.data[2] / mag])
        else:
            return Vector3([0, 0, 0])


class Object:
	"""
	Object is used for game objects.
	It hold all the needed values of a game object and has several functions for decluttering.
	"""
	def __init__(self):
		self.location = Vector3([0, 0, 0])
		self.velocity = Vector3([0, 0, 0])
		self.rotation = Vector3([0, 0, 0])
		self.angular_velocity = Vector3([0, 0, 0])

		self.local_angular_velocity = None
		self.matrix = None
		self.index = None

	def calculate_data(self):
		"""Calculates matrix and local_angular_velocity."""
		temps = Vector3(
		  [self.angular_velocity.data[0], self.angular_velocity.data[1], self.angular_velocity.data[2]])
		self.matrix = rotator_to_matrix(self)
		self.local_angular_velocity = Vector3([temps * self.matrix[1],
											   temps * self.matrix[2],
											   temps * self.matrix[0]])
	def to_local(self, target):
		"""Returns target's local position."""
		x = (to_location(target) - self.location) * self.matrix[0]
		y = (to_location(target) - self.location) * self.matrix[1]
		z = (to_location(target) - self.location) * self.matrix[2]
		return Vector3([x, y, z])

	def velocity2d(self):
		"""Returns own velocity."""
		return abs(self.velocity.data[0]) + abs(self.velocity.data[1])

	def distance_to_target_2d(self, target):
		"""Calculates 2d distance to target."""
		diff = self.location - to_location(target)
		return math.sqrt(diff.data[0]**2 + diff.data[1]**2)

	def angle_to_target(self, target):
		"""Returns angle to target between -pi and pi."""
		if isinstance(target, list):
			local_location = self.to_local(target)
			angle = math.atan2(to_location(local_location).data[1], to_location(local_location).data[0])
		else:
			angle = 0
		return angle


class Dodger:
	"""Class for decluttering dodging code."""
	def __init__(self, wait=2.2):
		"""'wait' is the wait period until next dodge is possible. Value is capped to be over 1"""
		self.timer = time.time()
		self.wait = max(wait, 1)

	def attempt_dodging(self):
		"""Dodges if time since last dodge is over wait. Returns jump and pitch"""
		time_difference = time.time() - self.timer
		if time_difference > self.wait:
			self.timer = time.time()
			jump, pitch = False, 0
		elif time_difference <= 0.1:
			jump, pitch = True, -1
		elif 0.1 <= time_difference <= 0.15:
			jump, pitch = False, -1
		elif 0.15 <= time_difference < 1:
			jump, pitch = True, -1
		else:
			jump, pitch = False, 0
		return jump, pitch
                                                                                  
                                                                                  
class SplinePathFinding:
    """A pathfinding script based on scipy's interpolate spline functions"""
    def __init__(self):
        self.stage = 0
        self.finished = False
        self.num_points = 0
        self.spline_locations = None
        self.spline_thresholds = None

    def run(self, agent, locations, thresholds, num_waypoints=63, dynamic=True):
        """
        Returns a Vector3 that is calculated based of a spline. When you reach that waypoint it moves to the next.
        This way you can get smooth rotation from position to position and reach each point from an angle you want.

        NOTE: You need to have a minimum of 4 locations and thresholds for this to work!

         - 'locations' is a list of Vector3's which the spline will touch in order.
         - 'thresholds' is a list of how close the bot should be to a waypoint before advancing to the next one.
         - 'num_points' is the amount of Vector3's you end up with. For a finer curve, use a higher number.
         - 'curve' is smoothing of the curve.

        For Example:
        If you want the car to hit the ball you set one location to the balls locations. Now you need 3 more.
        If you want to make sure you are covering your own goal before hitting th goal,
        you can set the first location to your goal.
        If you want the car to hit the ball towards the enemies goal you can set the last location to their goal.

        Advice:
        Don't have 4+ locations?
        If you don't have 4 locations, you can cheat a bit by duping locations, make sure to change it a little it.
        For example if the last location is the enemies goal [0, 5120 * -sign(agent.me.team), 0],
        you can make the last point a little further inside the goal [0, 5500 * -sign(agent.me.team), 0].
        """
        if len(locations) == len(thresholds):
            spline_waypoints, spline_thresholds = self.calculate(num_waypoints, locations, thresholds)

            try:
                if agent.me.distance_to_target_2d(spline_waypoints[self.stage]) \
                        <= spline_thresholds[self.stage]:
                    self.stage += 1
                elif dynamic and agent.me.distance_to_target_2d(spline_waypoints[self.stage - 1]) \
                        >= spline_thresholds[self.stage - 1]:
                    self.stage -= 1
            except IndexError:
                pass

            return Vector3(spline_waypoints[self.stage]).cap([-4000, -5000, 0], [4000, 5000, 2044])
        else:
            raise Exception("'locations' and 'thresholds' are different sizes. ({}, {])"
                            .format(len(locations), len(thresholds)))

    def calculate(self, num_points, locations, thresholds, curve_distance=20):
        """
        Calculates a spline (a series of Vector3's) called waypoints.
         - 'locations' is a list of Vector3's which the spline will touch in order.
         - 'thresholds' is a list of how close the bot should be to a waypoint before advancing to the next one.
         - 'num_points' is the amount of Vector3's you end up with. For a finer curve, use a higher number.
         - 'curve' is smoothing of the curve.
        """
        self.num_points = num_points

        distances = [0]
        for i in range(len(locations) - 1):
            try:
                distances.append(sum([abs(locations[i][0] - locations[i + 1][0]),
                                      abs(locations[i][1] - locations[i + 1][1])])
                                 + distances[i])
            except IndexError:
                distances.append(sum([abs(locations[i][0] - locations[i + 1][0]),
                                      abs(locations[i][1] - locations[i + 1][1])]))

        distances = [dist / (max(distances) / curve_distance) for dist in distances]

        xyz_locations = []
        for axis in range(len(locations[0])):
            xyz_locations.append([])
            for i in range(len(locations)):
                xyz_locations[axis].append(locations[i][axis])

        max_dist = (len(locations) - 1) * max(distances)
        increment = max_dist / (num_points - 1)

        points = []
        for i in range(num_points):
            points.append(i * increment)

        spline_locations_x = spline(points, xyz_locations[0], distances)
        spline_locations_y = spline(points, xyz_locations[1], distances)
        return [Vector3([x, y, 70]) for x, y in zip(spline_locations_x, spline_locations_y)],\
               spline(points, thresholds, distances)

def get_circle_points(num_points, radius):
	increment = 360 / num_points
	return [[radius * math.sin(x / num_points * -increment), radius * math.cos(y / num_points * increment)]
		   for x, y in zip(range(num_points), range(num_points))] +\
		   [[radius * math.sin(x * -increment), radius * math.cos(y * increment)]
		   for x, y in zip(range(num_points), range(num_points))]
                                                                                  
                                                                                  
def sign(x):
	"""Returns -1 if number is negative or zero, otherwise it return 1."""
	if x <= 0:
		return -1
	else:
		return 1

def to_location(target):
	if isinstance(target, Vector3):
		return target
	elif isinstance(target, list):
		return Vector3(target)
	elif isinstance(target, tuple):
		return Vector3(list(target))
	elif isinstance(target, np.ndarray):
		return Vector3(target.tolist())
	else:
		return target.location


def rotator_to_matrix(object):
	r = object.rotation.data
	CR = math.cos(r[2])
	SR = math.sin(r[2])
	CP = math.cos(r[0])
	SP = math.sin(r[0])
	CY = math.cos(r[1])
	SY = math.sin(r[1])

	matrix = []
	matrix.append(Vector3([CP*CY, CP*SY, SP]))
	matrix.append(Vector3([CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP * SR]))
	matrix.append(Vector3([-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR]))
	return matrix
    
def spline(points, locations, distances):
	tck = interpolate.splrep(distances, locations)
	return interpolate.splev(points, tck)
