"""Strategy: To find parking spot."""

import heapq
import random
import threading
from abc import abstractmethod

from panel import EntrancePanel
from parking_spot import ParkingSpot, ParkingSpotType


class FindParkingSpotStrategy:
    """Base Class: to find parking spot."""

    @abstractmethod
    def find_parking_spot(
        self,
        entrance_panel_id: int,
        spot_type: ParkingSpotType,
        free_spots: dict[ParkingSpot],
    ) -> int:
        """Find parking spot."""
        pass

    @abstractmethod
    def update_parking_spot_on_exit(self):
        """Update list of free spots on each vehicle's exit."""
        pass


class FindRandomSpotStrategy(FindParkingSpotStrategy):
    """Derived Class: Implements finding random free parking spot."""

    def find_parking_spot(
        self,
        entrance_panel_id: int,
        spot_type: ParkingSpotType,
        free_spots: dict[ParkingSpot],
    ) -> int:
        """Find the first free parking spot."""
        random_spot_id = random.choice(list(free_spots.keys()))
        return random_spot_id

    def update_parking_spot_on_exit(self):
        """Update list of free spots on each vehicle's exit."""
        return

    def __str__(self):
        return f"Find Random Spot Strategy"


class FindNearestSpotStrategy(FindParkingSpotStrategy):
    """Derived Class: Implements finding nearest free parking spot."""

    def __init__(
        self, entrance_panels: dict[int, EntrancePanel], free_spots, parking_spot_counts
    ):
        """Initalize instance of nearest parking spot strategy."""
        # Create min heaps of free parking spots for each of the entrance panels
        self.pq = {}
        self._lock = threading.Lock()
        for entrance_id, _ in entrance_panels.items():
            self.pq[entrance_id] = {}
            for spot_type in parking_spot_counts:
                self.pq[entrance_id][spot_type] = []
                for spot_id in free_spots[spot_type].keys():
                    # Simulate different orders of allotment at different entrances
                    # For odd numbered entrances, allot in decreasing order
                    if entrance_id % 2:
                        heapq.heappush(
                            self.pq[entrance_id][spot_type],
                            -spot_id,
                        )
                    # For even numbered entrances, allot in increasing order
                    else:
                        heapq.heappush(
                            self.pq[entrance_id][spot_type],
                            spot_id,
                        )

    def find_parking_spot(
        self,
        entrance_panel_id: int,
        spot_type: ParkingSpotType,
        free_spots: dict[ParkingSpot],
    ) -> int:
        """Find spot nearest to entrance.
        Running Time: O(|Num_Entrances|)
        """
        with self._lock:
            # Top of min heap is the nearest spot to entrance
            nearest_spot_id = self.pq[entrance_panel_id][spot_type][0]
            nearest_spot_id = abs(nearest_spot_id)

            # Remove this occupied spot from priority queue of all entrances
            for entrance_id in self.pq:
                if entrance_id % 2:
                    self.pq[entrance_id][spot_type].remove(-nearest_spot_id)
                else:
                    self.pq[entrance_id][spot_type].remove(nearest_spot_id)

        return nearest_spot_id

    def update_parking_spot(self, spot_id: int, spot_type: ParkingSpotType):
        """Update list of free spots on each vehicle's exit."""
        # Add this free spot to priority queue of all entrances
        with self._lock:
            for entrance_id in self.pq:
                if entrance_id % 2:
                    self.pq[entrance_id][spot_type].append(-spot_id)
                else:
                    self.pq[entrance_id][spot_type].append(spot_id)

    def __str__(self):
        return f"Find Nearest Spot Strategy"
