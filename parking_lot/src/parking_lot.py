"""Module: Parking Lot."""
import logging.config
import threading
import time
from collections import defaultdict
from concurrent import futures
from pathlib import Path

import yaml
from panel import DisplayBoard, EntrancePanel, ExitPanel
from parking_spot import ParkingSpot, ParkingSpotType
from parking_spot_strategy import FindNearestSpotStrategy, FindRandomSpotStrategy
from parking_ticket import ParkingTicket
from vehicle import Vehicle

logging.config.dictConfig(
    yaml.safe_load(Path("src/logs/logging_config.yaml").read_text())
)
logger = logging.getLogger(__name__)


class ParkingLot:
    """Class: Parking Lot."""

    def __init__(
        self,
        num_entrance_panels,
        num_exit_panels,
        num_display_boards,
        parking_spot_counts,
        parking_spot_rates_per_sec,
        vehicle_spot_type_mapping,
        find_parking_spot_strategy,
    ):
        """Initialize Parking Lot instance."""
        self._entrance_panels = {}
        self._exit_panels = {}
        self._display_boards = {}

        # Add entrance panels, exit panels, display boards
        self.add_entrance_panels(num_entrance_panels)
        self.add_exit_panels(num_exit_panels)
        self.add_display_boards(num_display_boards)

        # Add parking spots
        self._spots_free = defaultdict()
        self._spots_occupied = defaultdict()
        self._num_free_spots = defaultdict(int)
        self.add_parking_spots(parking_spot_counts)

        self._vehicle_spot_type_mapping = vehicle_spot_type_mapping
        self._rates_per_sec = parking_spot_rates_per_sec
        # Store all tickets for downstream analytics
        self._tickets = defaultdict(ParkingTicket)

        self._lock = threading.Lock()

        # Initializing strategis is done in a separate thread
        self._parking_spot_counts = parking_spot_counts
        self._find_parking_spot_strategy = find_parking_spot_strategy
        self._init_find_parking_spot_strategies()

        logger.info("***** Initialize Parking Lot with Settings *****")
        logger.info(f" Number of entrance panels: {len(self._entrance_panels)}")
        logger.info(f" Number of exit panels: {len(self._exit_panels)}")
        logger.info(f" Number of display boards: {len(self._display_boards)}")
        for spot_type, num_spots in self._num_free_spots.items():
            logger.info(f"{spot_type}: {num_spots} total spots available.")
        logger.info(f" Find parking spot strategy: {self._find_parking_spot_strategy}")
        for spot_type, spot_rate in self._rates_per_sec.items():
            logger.info(f"{spot_type}: {spot_rate} unit per sec.")
        logger.info("************************************************")

    def _init_find_parking_spot_strategies(self):
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures_map = {}  # Map<Strategy, Future>
            futures_map["first"] = executor.submit(FindRandomSpotStrategy)
            futures_map["nearest"] = executor.submit(
                FindNearestSpotStrategy,
                self._entrance_panels,
                self._spots_free,
                self._parking_spot_counts,
            )

            futures.as_completed(futures_map)

            self._find_parking_spot_strategies = {}  # Map<Strategy, strategy instance>
            # Iterate over futures as result becomes available
            for strategy, future in futures_map.items():
                self._find_parking_spot_strategies[strategy] = future.result()

            self._find_parking_spot_strategy = self._find_parking_spot_strategies[
                self._find_parking_spot_strategy
            ]

        return

    def add_parking_spots(self, parking_spot_counts: dict[ParkingSpotType, int]):
        """Add parking spots of different types."""
        acc_num_spots = 0
        for spot_type, num_spots in parking_spot_counts.items():
            self._spots_free[spot_type] = {}

            for i in range(num_spots):
                spot_id = acc_num_spots + i
                self._spots_free[spot_type][spot_id] = ParkingSpot(
                    floor=0, spot_id=spot_id, spot_type=spot_type
                )

            self._spots_occupied[spot_type] = {}
            self._num_free_spots[spot_type] = num_spots
            acc_num_spots += num_spots

    def add_entrance_panels(self, num_entrance_panels: int):
        """Add entrance panels."""
        for i in range(num_entrance_panels):
            self._entrance_panels[i] = EntrancePanel(panel_id=i)

    def add_exit_panels(self, num_exit_panels: int):
        """Add exit panel."""
        for i in range(num_exit_panels):
            self._exit_panels[i] = ExitPanel(panel_id=i)

    def add_display_boards(self, num_display_boards: int):
        """Add display boards."""
        for i in range(num_display_boards):
            self._display_boards[i] = DisplayBoard(board_id=i)

    def notify_display_boards(self):
        """Update display boards with number of free spot counts."""
        for i in range(len(self._display_boards)):
            self._display_boards[i].update_num_free_spot_counts(self._num_free_spots)

    def get_parking_spot(
        self, entrance_panel_id: int, spot_type: ParkingSpotType, vehicle: Vehicle
    ) -> None | ParkingSpot:
        """Find parking spot
        Args:
            entrance_panel_id (int): Unique ID of entrance panel
            spot_type (Enum): ParkingSpotType
            vehicle (Vehicle): Instance of vehicle class
        Returns:
            parking_spot (None | ParkingSpot)
        """
        parking_spot = None

        # Acquire lock
        with self._lock:
            # If parking spots for this vehicle type is full, return None (no ticket assigned)
            if not self._num_free_spots[spot_type]:
                logger.info(f"Parking Spots for {vehicle.vehicle_type} are full")
                return parking_spot

            """Get parking spot."""
            spot_id = self._find_parking_spot_strategy.find_parking_spot(
                entrance_panel_id, spot_type, self._spots_free[spot_type]
            )

            # Get the parking spot for this spot_id
            parking_spot = self._spots_free[spot_type][spot_id]
            # Assign vehicle to this spot
            parking_spot.assign_vehicle(vehicle=vehicle)

            # Remove this spot from free spots and add it to occupied spots
            self._spots_free[spot_type].pop(spot_id)
            self._spots_occupied[spot_type][spot_id] = parking_spot
            self._num_free_spots[spot_type] -= 1
        # Release lock

        return parking_spot

    def handle_vehicle_entrance(
        self, entrance_panel_id: int, vehicle: Vehicle
    ) -> ParkingTicket | None:
        logger.info(
            f"Vehicle: Type: {vehicle.vehicle_type}, Vehicle ID: {vehicle.vehicle_id} at entrance panel id:{entrance_panel_id}"
        )
        """Handle vehicle at entrance panel."""
        if entrance_panel_id >= len(self._entrance_panels):
            raise ValueError("entrance_panel_id is out of bounds")

        # Get the mapping to appropriate parking spot type for this vehicle
        spot_type = self._vehicle_spot_type_mapping[vehicle.vehicle_type]

        # Get parking spot for current vehicle
        parking_spot = self.get_parking_spot(entrance_panel_id, spot_type, vehicle)

        # If parking spots for this vehicle type is full, return None (no ticket assigned)
        if not parking_spot:
            return None

        logger.info(f"Assigned {spot_type} with id:{parking_spot.spot_id}")

        # Issue ticket
        parking_ticket = self._entrance_panels[entrance_panel_id].issue_ticket(
            vehicle=vehicle, parking_spot=parking_spot
        )
        # Assign ticket to vehicle
        vehicle.ticket = parking_ticket

        logger.info(
            f"Ticket assigned, ID:{parking_ticket.ticket_id} at {parking_ticket.issued_at}"
        )

        # Updating display boards with latest counts
        self.notify_display_boards()

        return parking_ticket

    def handle_vehicle_exit(
        self,
        exit_panel_id: int,
        vehicle: Vehicle,
    ):
        """Handle vehicle's exit
        Scan Ticket
        Accept Payment.
        """

        if exit_panel_id >= len(self._exit_panels):
            raise ValueError("exit_panel_id is out of bounds")

        # Scan ticket and handle payment
        ticket = self._exit_panels[exit_panel_id].scan_ticket(
            ticket=vehicle.ticket, rates=self._rates_per_sec
        )
        # Save ticket (in DB) for downstream analytics
        self._tickets[ticket.ticket_id] = ticket

        logger.info(
            f"Vehicle: Type: {ticket.vehicle_type}, Vehicle ID: {ticket.vehicle_id} at exit panel id:{exit_panel_id}"
        )

        # Acquire lock
        with self._lock:
            # Remove this spot from occupied spots and add it to free spots
            spot_id = ticket.spot_id
            spot_type = ticket.spot_type
            parking_spot = self._spots_occupied[spot_type][spot_id]
            self._spots_occupied[spot_type].pop(spot_id)
            self._spots_free[spot_type][spot_id] = parking_spot
            self._num_free_spots[spot_type] += 1
            self.notify_display_boards()

            # Update list of free spots in find parking spot strategies
            self._find_parking_spot_strategy.update_parking_spot(spot_id, spot_type)
        # Release lock

        logger.info(f"Spot freed: {ticket.spot_type} with id:{ticket.spot_id}")
        logger.info(
            f"Ticket scanned, ID:{ticket.ticket_id}. Payment of {ticket.paid_amount} handled at {ticket.paid_at}"
        )

        return
