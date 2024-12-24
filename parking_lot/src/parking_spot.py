"""Module: Parking spot."""

from enum import Enum

from vehicle import Vehicle


class ParkingSpotType(Enum):
    """Types of Parking Spots."""

    HANDICAPPED = "handicapped"
    COMPACT = "compact"
    LARGE = "large"
    MOTORBIKE = "motorbike"


class ParkingSpot:
    """Class: Parking Spot."""

    def __init__(self, floor: int, spot_id: int, spot_type: ParkingSpotType):
        """Initialize Vehicle instance.

        Args:
            floor (int): Floor number
            spot_id (int): Parking spot number
            spot_type (Enum): Parking spot type Enum
        """
        self._floor = floor
        self.spot_id = spot_id
        self._free = True
        self._vehicle = None
        self.spot_type = spot_type

    def assign_vehicle(self, vehicle: Vehicle):
        """Assign vehicle to parking spot.

        Args:
            vehicle (Vehicle): Vehicle Instance
        """
        self._vehicle = vehicle
        self._free = False

    def remove_vehicle(self):
        """Remove vehicle from parking spot."""
        self._vehicle = None
        self._free = True


class HandicappedSpot(ParkingSpot):
    """Class: Handicapped Parking Spot."""

    def __init__(self, number: int):
        """Initialize handicapped parking spot."""
        super().__init__(number, ParkingSpotType.HANDICAPPED)


class CompactSpot(ParkingSpot):
    """Class: Handicapped Parking Spot."""

    def __init__(self, number: int):
        """Initialize handicapped parking spot."""
        super().__init__(number, ParkingSpotType.COMPACT)


class LargeSpot(ParkingSpot):
    """Class: Large Parking Spot."""

    def __init__(self, number: int):
        """Initialize large parking spot."""
        super().__init__(number, ParkingSpotType.LARGE)


class MotorbikeSpot(ParkingSpot):
    """Class: Motorbike Parking Spot."""

    def __init__(self, number: int):
        """Initialize motorbike parking spot."""
        super().__init__(number, ParkingSpotType.MOTORBIKE)
