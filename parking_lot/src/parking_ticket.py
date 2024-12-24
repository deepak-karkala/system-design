"""Module: Parking Ticket."""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import vehicle
from parking_spot import ParkingSpotType
from pydantic import BaseModel


class ParkingTicketStatus(Enum):
    """Enum: ParkingTicketStatus."""

    UNPAID = "unpaid"
    PAID = "paid"
    LOST = "lost"


class ParkingTicket(BaseModel):
    """Class: Parking Ticket."""

    ticket_id: UUID = uuid4()
    entrance_id: int
    spot_id: int
    spot_type: ParkingSpotType
    vehicle_id: int
    vehicle_type: vehicle.VehicleType
    issued_at: datetime
    paid_at: datetime | None
    exit_id: int | None
    status: ParkingTicketStatus
    paid_amount: float | None
