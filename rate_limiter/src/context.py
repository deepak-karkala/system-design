from rate_limiter import RateLimiter


class Context:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    def add_users(self, users):
        for user in users:
            self.rate_limiter.add_user(
                user["user_id"], user["num_requests"], user["window_time_in_sec"]
            )

    def send_request(self, user_id):
        return (
            "HTTP 200"
            if self.rate_limiter.is_allowed(user_id)
            else "HTTP 429: Too Many Requests"
        )
