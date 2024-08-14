from abc import ABCMeta, abstractmethod


class RateLimiter:
    """
    Interface for Rate Limiters
    """

    @abstractmethod
    def add_user(self, user_id, num_requests, window_time_in_sec):
        pass

    @abstractmethod
    def remove_user(self, user_id):
        pass

    @abstractmethod
    def is_allowed(self, user_id):
        pass
