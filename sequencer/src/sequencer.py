import threading
import time
from abc import ABCMeta, abstractmethod
from typing import Final


class Sequencer:
    """
    Interface for Sequencers (Distributed UID generators)
    """

    @abstractmethod
    def generate_id(self, node_id: int):
        pass


class SnowflakeSequencer(Sequencer):
    """
    Implementation of Twitter Snowflake ID generator
    Adapted from: https://www.callicoder.com/distributed-unique-id-sequence-number-generator/
    """

    def __init__(self):
        self.UNUSED_BITS: Final[int] = 1
        self.EPOCH_BITS: Final[int] = 41
        self.NODE_ID_BITS: Final[int] = 10
        self.SEQUENCE_BITS: Final[int] = 12
        self.EPOCH: Final[int] = 1420070400000
        self.MAX_SEQUENCE = 2**self.SEQUENCE_BITS - 1
        self.MAX_NODE_ID = 2**self.NODE_ID_BITS - 1
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def get_timestamp_since_epoch_ms(self):
        return round(time.time() * 1000) - self.EPOCH

    def wait_till_next_ms(self, current_timestamp):
        """
        Block till next ms is generated,
        used when sequence IDs are exhausted for current ms
        """
        while current_timestamp == self.last_timestamp:
            current_timestamp = self.get_timestamp_since_epoch_ms()
        return current_timestamp

    def generate_id(self, node_id: int):
        with self.lock:
            print(node_id)
            print(self.MAX_NODE_ID)
            if node_id < 0 or node_id > self.MAX_NODE_ID:
                raise ValueError("node_id must be between 0 and {self.MAX_NODE_ID}")

            current_timestamp = self.get_timestamp_since_epoch_ms()
            if current_timestamp < self.last_timestamp:
                raise ValueError("Non monotonically increasing system clock")

            # If same timestamp (ms), increment sequence ID
            if current_timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) % self.MAX_SEQUENCE
                # Sequence exhausted in current ms, wait till next ms
                if self.sequence == 0:
                    current_timestamp = wait_till_next_ms(current_timestamp)
            # If current timestamp is new ms, start sequence ID at 0
            else:
                self.sequence = 0

            self.last_timestamp = current_timestamp

            uid = current_timestamp << (self.NODE_ID_BITS + self.SEQUENCE_BITS)
            uid |= node_id << self.SEQUENCE_BITS
            uid |= self.sequence

        return uid
