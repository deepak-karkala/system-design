"""Module: Entrance, Exit Panels."""
import logging.config
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import yaml
from parking_spot import ParkingSpot
from parking_ticket import ParkingTicket, ParkingTicketStatus
from vehicle import Vehicle

logger = logging.getLogger(__name__)


class EntrancePanel:
    """Class: Entrance Panel."""

    def __init__(self, panel_id: int):
        """Initialize entrance panel instance."""
        self._panel_id = panel_id

    def issue_ticket(
        self, vehicle: Vehicle, parking_spot: ParkingSpot
    ) -> ParkingTicket:
        """Issue ticket to vehicle."""
        parking_ticket = ParkingTicket(
            ticket_id=uuid4(),
            entrance_id=self._panel_id,
            spot_id=parking_spot.spot_id,
            spot_type=parking_spot.spot_type,
            vehicle_id=vehicle.vehicle_id,
            vehicle_type=vehicle.vehicle_type,
            issued_at=datetime.now(),
            paid_at=None,
            exit_id=None,
            status=ParkingTicketStatus.UNPAID,
            paid_amount=None,
        )
        return parking_ticket


class ExitPanel:
    """Class: Exit Panel."""

    def __init__(self, panel_id: int):
        """Initialize exit panel instance."""
        self._panel_id = panel_id

    def scan_ticket(self, ticket: ParkingTicket, rates):
        """Scan ticket at exit."""
        current_timestamp = datetime.now()
        seconds_elapsed = (current_timestamp - ticket.issued_at).seconds
        total_amount = rates[ticket.spot_type] * seconds_elapsed

        # Accept payment and update ticket payment status
        ticket.paid_at = current_timestamp
        ticket.exit_id = self._panel_id
        ticket.status = ParkingTicketStatus.PAID
        ticket.paid_amount = total_amount

        return ticket


class DisplayBoard:
    """Class:Display board."""

    def __init__(self, board_id: int):
        """Initialize display board instance."""
        self._board_id = board_id

    def update_num_free_spot_counts(self, num_free_spots):
        """Update count of free spots."""
        logger.info(f"DisplayBoard{self._board_id}: ")
        for spot_type, free_spots in num_free_spots.items():
            logger.info(f"{spot_type}: {free_spots} free spots available.")
