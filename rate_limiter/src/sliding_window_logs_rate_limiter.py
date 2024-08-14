import threading
import time
from collections import deque

from rate_limiter import RateLimiter


class UserLog:
    """
    Log of each user's request timestamps
    """

    def __init__(self, num_requests, window_time_in_sec):
        self.lock = threading.Lock()
        self.num_requests = num_requests
        self.window_time_in_sec = window_time_in_sec
        self.log = deque()

    def evict_older_timestamps(self, current_timestamp):
        """
        Removing timestamps that are older than current window
        """
        while self.log and current_timestamp - self.log[0] > self.window_time_in_sec:
            self.log.popleft()


class SlidingWindowLogsRateLimiter(RateLimiter):
    """
    Implemenatation of Sliding window Log rate limiter
    Ref: https://medium.com/@saisandeepmopuri/system-design-rate-limiter-and-data-modelling-9304b0d18250
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.user_log_map = {}

    @classmethod
    def get_current_timestamp_sec(cls):
        return int(round(time.time()))

    def add_user(self, user_id, num_requests, window_time_in_sec):
        with self.lock:
            if user_id in self.user_log_map:
                raise Exception("User already present")
            self.user_log_map[user_id] = UserLog(num_requests, window_time_in_sec)

    def remove_user(self, user_id):
        with self.lock:
            if user_id in self.user_log_map:
                del self.user_log_map[user_id]

    def is_allowed(self, user_id):
        with self.lock:
            if user_id not in self.user_log_map:
                raise Exception("User not present")
            user_log = self.user_log_map[user_id]

        with user_log.lock:
            current_timestamp = SlidingWindowLogsRateLimiter.get_current_timestamp_sec()
            # Remove older timestamps beyond current window
            user_log.evict_older_timestamps(current_timestamp)
            # Append current request's timestamp to user log
            user_log.log.append(current_timestamp)
            # Check if number of requests in current window is less than the rate defined
            if len(user_log.log) > user_log.num_requests:
                return False
            return True
