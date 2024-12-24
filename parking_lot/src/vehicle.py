"""Module: Vehicle and vehicle types."""

from abc import ABC, abstractmethod
from enum import Enum


class VehicleType(str, Enum):
    """Types of vehicles."""

    CAR = "car"
    TRUCK = "truck"
    MOTORBIKE = "motorbike"


class Vehicle:
    """Class: Vehicle."""

    def __init__(self, vehicle_id: int, vehicle_type: VehicleType):
        """Initializes Vehicle instance

        Args:
            vehicle_id (int): Unique identifier of vehicle
            vehicle_type (Enum): Vehicle type Enum
        """
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.ticket = None

    def __str__(self):
        class_name = type(self).__name__
        return f"{class_name}(vehicle_id={self.vehicle_id}, vehicle_type={self.vehicle_type})"


class Car(Vehicle):
    """Class: Car."""

    def __init__(self, vehicle_id: int):
        super().__init__(vehicle_id, VehicleType.CAR)


class Truck(Vehicle):
    """Class: Truck."""

    def __init__(self, vehicle_id: int):
        super().__init__(vehicle_id, VehicleType.TRUCK)


class Motorbike(Vehicle):
    """Class: Motorbike."""

    def __init__(self, vehicle_id: int):
        super().__init__(vehicle_id, VehicleType.MOTORBIKE)


class Factory(ABC):
    """Class: Factory to create vehicle instances."""

    @abstractmethod
    def factory_method(self, vehicle_id) -> Vehicle:
        pass


class CarFactory(Factory):
    def factory_method(self, vehicle_id) -> Vehicle:
        return Car(vehicle_id)


class MotorbikeFactory(Factory):
    def factory_method(self, vehicle_id) -> Vehicle:
        return Motorbike(vehicle_id)


class TruckFactory(Factory):
    def factory_method(self, vehicle_id) -> Vehicle:
        return Truck(vehicle_id)
