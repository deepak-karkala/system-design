import logging
import time

import typer
from context import Context
from rate_limiter import RateLimiter
from sliding_window_logs_rate_limiter import SlidingWindowLogsRateLimiter
from typing_extensions import Annotated

logging.basicConfig(level=logging.DEBUG)
app = typer.Typer()


@app.command()
def rate_limiter_app(
    rate_limiter_algorithm: Annotated[
        str, typer.Option(help="Rate Limiter algorithm Options 0: Sliding Window Log")
    ] = None,
):
    # Init Rate Limiter Implementation
    rate_limiter = SlidingWindowLogsRateLimiter()
    # Init context
    context = Context(rate_limiter)

    # Add users
    users = [
        {"user_id": "user1", "num_requests": 2, "window_time_in_sec": 30},
        {"user_id": "user2", "num_requests": 3, "window_time_in_sec": 30},
    ]
    context.add_users(users)

    # Send requests and see if they are throttled beyond limit
    logging.info(context.send_request(user_id="user1"))
    time.sleep(5)
    logging.info(context.send_request(user_id="user1"))
    time.sleep(5)
    logging.info(context.send_request(user_id="user1"))
    time.sleep(30)
    logging.info(context.send_request(user_id="user1"))


if __name__ == "__main__":
    app()
