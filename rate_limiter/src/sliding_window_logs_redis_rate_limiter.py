import time

import redis
from rate_limiter import RateLimiter


class SlidingWindowLogsRedisRateLimiter(RateLimiter):
    """
    Implemenatation of Sliding window Log rate limiter
        Representation of data stored in redis
        metadata
        --------
        "userid_metadata": {
                "requests": 2,
            "window_time": 30
        }

        timestamps
        ----------
        "userid_timestamps": sorted_set([
            "ts1": "ts1",
            "ts2": "ts2"
        ])
    Ref: https://medium.com/@saisandeepmopuri/system-design-rate-limiter-and-data-modelling-9304b0d18250
    """

    METADATA_SUFFIX = "_metadata"
    TIMESTAMPS_SUFFIX = "_timestamps"

    def __init__(self):
        self.conn = get_connection()

    @classmethod
    def get_current_timestamp_sec(cls):
        return int(round(time.time()))

    def add_user(self, user_id, num_requests, window_time_in_sec):
        self.conn.hset(
            user_id + self.METADATA_SUFFIX,
            {"requests": num_requests, "window_time": window_time_in_sec},
        )

    def remove_user(self, user_id):
        self.conn.delete(
            user_id + self.METADATA_SUFFIX, user_id + self.TIMESTAMPS_SUFFIX
        )

    # get the user metadata (number of requests, window time)
    def get_user_rate(self, user_id):
        val = self.con.hgetall(user_id + self.METADATA_SUFFIX)
        if val is None:
            raise Exception("Un-registered user: " + user_id)
        return int(val["requests"]), int(val["window_time"])

    def add_timestamp_atomically_and_return_size(self, user_id, timestamp):
        """
        # Atomically add an element to the timestamps and return the total number of requests
        # in the current window time.
        # Transaction holds an optimistic lock over the redis entries userId + self.METADATA_SUFFIX
        # and userId + self.TIMESTAMPS. The changes in _addNewTimestampAndReturnTotalCount
        # are committed only if none of these entries get changed through out
        """
        _, size = self.conn.transaction(
            lambda pipe: self._add_new_timestamp_and_return_total_count(
                user_id, timestamp, pipe
            ),
            user_id + self.METADATA_SUFFIX,
            user_id + self.TIMESTAMPS_SUFFIX,
        )
        return size

    def _add_new_timestamp_and_return_total_count(
        self, user_id, timestamp, redis_pipeline
    ):
        """
        # A two element array with first one representing success of adding an element into
        # sorted set and other as the count of the sorted set is returned by this method
        """
        redis_pipeline.multi()
        redis_pipeline.zadd(user_id + self.TIMESTAMPS_SUFFIX, timestamp, timestamp)
        redis_pipeline.zcount(user_id + self.TIMESTAMPS_SUFFIX, 0, self.INF)

    def is_allowed(self, user_id):
        """
        # decide to allow a service call or not
        # we use sorted sets datastructure in redis for storing our timestamps.
        """
        max_requests, unit_time = self.get_user_rate(user_id)
        current_timestamp = self.get_current_timestamp_sec()
        # evict older entries
        oldest_possible_entry = current_timestamp - unit_time
        # removes all the keys from start to oldest bucket
        self.con.zremrangebyscore(
            user_id + self.TIMESTAMPS_SUFFIX, 0, oldest_possible_entry
        )
        current_request_count = self.add_timestamp_atomically_and_return_size(
            user_id, current_timestamp
        )
        if current_request_count > max_requests:
            return False
        return True
