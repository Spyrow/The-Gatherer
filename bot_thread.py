import threading
from time import sleep
import time
import pyautogui
import random
import math
import cv2
import numpy
import win32api
from window_capture import get_game_rect

#Don't let a FailSafeException (mouse touching a screen corner) kill the bot thread
pyautogui.FAILSAFE = False

#Minimum pixels the clicked node has to move for the player to be considered walking
MOVE_THRESHOLD = 12
#Number of blocked attempts before moving somewhere else
BLOCKED_LIMIT = 8
#Pixels before a target is considered reached
AT_TARGET = 35
#Gather cycles done at a waypoint before moving to the next one
GATHER_LOOPS = 5
#Travel clicks per waypoint, retried only while the player did not actually move
WALK_ATTEMPTS = 3

#Recorded route, a list of [x, y] screen positions clicked while recording
ROUTE = []

def get_center(rectangles):
    centers = []
    for i in rectangles:
        x = int((i[0]+(i[0]+i[2]))/2)
        y = int((i[1]+(i[1]+i[3]))/2)
        centers.append([x, y])
        #print(centers)
    return centers


def get_rectangles(results):
    rectangles = []
    x = results.xyxy[0].tolist()
    for i in x:
        rectangles.append(i[:-2])
    return rectangles


class Move:
	def __init__(self):
		#Lock the thread
		self.lock = threading.Lock()
		#Obstacle handling counter
		self.stuck_count = 0
		#Route mode
		self.recording = False
		self.follow = False
		self.route_i = 0
		self.gather_cycles = 0
		self.gathering_at_waypoint = False
		self.travelled = False
		self.lmb_was_down = False
		self.paused = False


		
	def nearest_object(self, screen_center):
		dictionary = {}
		for i in range(len(self.centers)):
			object_location = self.centers[i]
			#Calculate distance between an object and the character
			distance = math.dist(object_location, screen_center)
			#Add result to dictionary
			dictionary[i] = distance 

		#print(dictionary)
		sort_dictionary = sorted(dictionary, key=dictionary.get, reverse=False)
		closest_object = self.centers[sort_dictionary[0]]
		return closest_object

	#Return an approach point offset sideways to walk around the obstacle
	def _deflect(self, target, screen_center, tries=None):
		vx = target[0] - screen_center[0]
		vy = target[1] - screen_center[1]
		length = math.hypot(vx, vy)
		if length < 1:
			return target
		if tries is None:
			tries = self.stuck_count
		nx, ny = vx / length, vy / length
		px, py = -ny, nx
		side = 1 if tries % 2 == 0 else -1
		advance = min(0.4 * length, 90)
		return [int(screen_center[0] + nx * advance + px * 65 * side),
			int(screen_center[1] + ny * advance + py * 65 * side)]


	#Check if the player is already standing on the target
	def _at_target(self, target, screen_center):
		return math.dist([target[0], target[1]], [screen_center[0], screen_center[1]]) < AT_TARGET


	#Sleep in small slices so a pause/stop request interrupts it quickly
	def pause_sleep(self, seconds):
		end = time.time() + seconds
		while time.time() < end:
			if self.paused or self.stopped:
				return
			sleep(0.2)


	#Sleep while state==0 but wake up immediately if the bot resumes
	def wait_state(self, seconds):
		end = time.time() + seconds
		while time.time() < end and self.state == 0:
			sleep(0.1)


	#Check if the clicked node moved, meaning the player actually walked toward it
	def _has_moved(self, old_pos, frame_centers):
		if not frame_centers:
			return True
		best_d = 1e9
		for c in frame_centers:
			d = math.dist([c[0], c[1]], [old_pos[0], old_pos[1]])
			if d < best_d:
				best_d = d
		return best_d > MOVE_THRESHOLD


	#Walk toward the current route waypoint. The camera is locked on the player, so one
	#click walks the whole way: clicking the same pixel again would move it a second
	#time by the same offset and overshoot. Returns True if the scenery shifted,
	#meaning the player actually moved (or it cannot be told).
	def _walk_to(self, waiting_time, waypoint, screen_center):
		print(f"Walking to waypoint {self.route_i + 1}/{len(ROUTE)}: {waypoint[0]}, {waypoint[1]}")
		before = [list(c) for c in self.centers]
		pyautogui.moveTo(waypoint[0], waypoint[1], duration=0.5)
		pyautogui.click(button="left")
		self.pause_sleep(waiting_time)

		if not before or not self.centers:
			return True
		now = [list(c) for c in self.centers]
		for old in before:
			if min(math.dist(old, c) for c in now) > MOVE_THRESHOLD:
				return True
		return False


	#At a waypoint: mine the nearest detected resource until the spot is cleared
	def _gather_at_waypoint(self, waiting_time, screen_center):
		if not self.centers:
			print("No resources at this waypoint")
			self.gather_cycles += 1
			self.pause_sleep(waiting_time)
			return

		closest_object = self.nearest_object(screen_center)

		#On the node already, keep mining
		if self._at_target(closest_object, screen_center):
			self.stuck_count = 0
			self.gather_cycles += 1
			print(f"Gathering at waypoint {self.route_i + 1}...")
			self.pause_sleep(waiting_time)
			return

		#Walk to the node, deflecting if something is blocking the path
		if self.stuck_count > 0:
			click_point = self._deflect(closest_object, screen_center)
		else:
			click_point = closest_object

		print(f"Moving to resource: {click_point[0]}, {click_point[1]}")
		pyautogui.moveTo(click_point[0], click_point[1], duration=0.5)
		pyautogui.click(button="left")
		self.pause_sleep(waiting_time)

		if self._has_moved(closest_object, self.centers):
			self.stuck_count = 0
		else:
			self.stuck_count += 1
			print(f"Potential obstacle while gathering (attempt {self.stuck_count})")

		#Node unreachable, count it as handled and move on
		if self.stuck_count >= BLOCKED_LIMIT:
			self.stuck_count = 0
			self.gather_cycles += 1


	#Follow the recorded route in order: first reach the waypoint, then gather
	def go_route(self, waiting_time, screen_center):
		if not ROUTE:
			print("Route is empty")
			return

		#Travel phase: click the current waypoint until the player actually moves
		if not self.travelled:
			waypoint = ROUTE[self.route_i]
			attempts = 0
			moved = False
			while attempts < WALK_ATTEMPTS and not moved and not self.paused and not self.stopped:
				moved = self._walk_to(waiting_time, waypoint, screen_center)
				attempts += 1
			self.travelled = True
			if self.paused or self.stopped:
				return
			print(f"At waypoint {self.route_i + 1}/{len(ROUTE)}")

		#Always gather at the waypoint: a visible resource is mined, otherwise the
		#empty-spot counter moves on to the next waypoint
		if not self.gathering_at_waypoint:
			self.gathering_at_waypoint = True

		#Gathering phase: leaves only when the spot is cleared or the time is up
		if self.gathering_at_waypoint:
			self._gather_at_waypoint(waiting_time, screen_center)

			leave = False
			if not self.centers and self.gather_cycles >= 2:
				print("Spot cleared, moving to next waypoint")
				leave = True
			elif self.gather_cycles >= GATHER_LOOPS:
				print("Gathering time over, moving to next waypoint")
				leave = True

			if leave:
				self.gather_cycles = 0
				self.gathering_at_waypoint = False
				self.next_waypoint()
			return


	def next_waypoint(self):
		self.route_i = (self.route_i + 1) % len(ROUTE)
		self.gathering_at_waypoint = False
		self.travelled = False
		print(f"Next waypoint: {self.route_i + 1}/{len(ROUTE)}")


	#Reset route progress so the route starts again from the first waypoint
	def reset_route_state(self):
		self.route_i = 0
		self.gather_cycles = 0
		self.gathering_at_waypoint = False
		self.travelled = False
		self.stuck_count = 0


	#Move player to mine rock
	def go_to(self, waiting_time, screen_center):
		b = 0
		rand_pos = [[660, 500], [424, 226]]

		if len(self.centers)>0:
			print(f"Waiting {waiting_time} seconds")
			#Find the closest object to the player
			closest_object = self.nearest_object(screen_center)
			print(closest_object)

			#Already on the node, keep mining and reset the obstacle counter
			if self._at_target(closest_object, screen_center):
				self.stuck_count = 0
				print("Already on target")
				self.pause_sleep(waiting_time)
				return

			#Click the node, or deflect sideways if the last attempt was blocked
			if self.stuck_count > 0:
				click_point = self._deflect(closest_object, screen_center)
				print(f"Obstacle, clicking around: {click_point[0]}, {click_point[1]}")
			else:
				click_point = closest_object

			#Display moving position
			print(f"Moving to: {click_point[0]}, {click_point[1]}")

			#Action 1 (Move mouse)
			pyautogui.moveTo(click_point[0],click_point[1],duration=0.5)
			print("click\n")
			#Action 2 (Movement click)
			pyautogui.click(button="left")
			self.pause_sleep(waiting_time)

			#Check if the player actually moved toward the target after the click
			if self._has_moved(closest_object, self.centers):
				self.stuck_count = 0
			else:
				self.stuck_count += 1
				print(f"Potential obstacle, going around (attempt {self.stuck_count})")

			#Too many blocked attempts, move somewhere else and restart
			if self.stuck_count >= BLOCKED_LIMIT:
				print("Too many attempts, moving to a new spot")
				self.stuck_count = 0
				pyautogui.moveTo(rand_pos[b][0],rand_pos[b][1],duration=0.5)
				pyautogui.click(button="left")
				self.pause_sleep(2.5)

		else:
			print(f"Waiting 2.5 seconds")
			print("No results")
			#Choose "random" position to move
			b = random.randint(0,1)
			self.stuck_count = 0
			
			#Display moving position
			print(f"Stuck, moving to: {rand_pos[b][0]}, {rand_pos[b][1]}")
			
			#Action 1 (Move mouse)
			pyautogui.moveTo(rand_pos[b][0],rand_pos[b][1],duration=0.5)
			print("click\n")

			
			#Action 2 (Movement click)
			pyautogui.click(button="left")
			self.pause_sleep(2.5)
			
			#Reset var
			b = 0

    #Thread Functions
	def start(self):
		self.stopped = False
		self.state = 0
		self.t = threading.Thread(target=self.run)
		self.t.start()
    
	def update(self, centers, bot_status, waiting_time, screen_center):
		self.screen_center = screen_center
		self.waiting_time = waiting_time
		#print(f"Bot Status Thread: {bot_status}")
		if bot_status==True:
			self.state = 1
			self.paused = False
		elif bot_status==False:
			self.state = 0
			self.paused = True
		self.centers = centers


	def stop(self):
		self.stopped = True
		print("Terminating...")


	def run(self):
		while not self.stopped:
			#Capture user clicks as route waypoints while recording is enabled
			if self.recording:
				lmb_down = win32api.GetAsyncKeyState(0x01) & 0x8000
				if lmb_down and not self.lmb_was_down:
					x, y = pyautogui.position()
					rect = get_game_rect()
					if rect is None or (rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]):
						ROUTE.append([int(x), int(y)])
						print(f"Waypoint {len(ROUTE)}: {x}, {y}")
					else:
						print(f"Ignored click at {x}, {y}: outside the game window (record clicks inside Albion)")
				self.lmb_was_down = lmb_down

			if self.state == 0:
				self.wait_state(0.05 if self.recording else 3)

			elif self.state == 1:
				self.lock.acquire()
				try:
					if self.follow and ROUTE:
						self.go_route(self.waiting_time, self.screen_center)
					else:
						self.go_to(self.waiting_time, self.screen_center)
				except Exception as e:
					print(f"Bot error (continuing): {e}")
				finally:
					self.lock.release()
