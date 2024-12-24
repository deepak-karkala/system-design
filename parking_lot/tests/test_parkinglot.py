"""Test Parking lot's vehicle entry and exit scenarios."""
import logging.config
import time
from concurrent import futures

import pytest
from parking_lot import ParkingLot
from parking_spot import ParkingSpotType
from vehicle import Car, CarFactory, Vehicle, VehicleType

logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def parking_spot_counts():
    def _parking_spot_counts(num_spots):
        return {
            ParkingSpotType.COMPACT: num_spots,
            ParkingSpotType.MOTORBIKE: 50,
            ParkingSpotType.LARGE: 15,
            ParkingSpotType.HANDICAPPED: 5,
        }

    return _parking_spot_counts


@pytest.fixture(scope="class")
def parking_spot_rates_per_sec():
    return {
        ParkingSpotType.MOTORBIKE: 0.0025,
        ParkingSpotType.COMPACT: 0.005,
        ParkingSpotType.LARGE: 0.01,
        ParkingSpotType.HANDICAPPED: 0.002,
    }


@pytest.fixture(scope="class")
def vehicle_spot_type_mapping():
    return {
        VehicleType.CAR: ParkingSpotType.COMPACT,
        VehicleType.TRUCK: ParkingSpotType.LARGE,
        VehicleType.MOTORBIKE: ParkingSpotType.MOTORBIKE,
    }


@pytest.fixture(scope="class")
def num_spots(request):
    return request.param


@pytest.fixture(scope="class")
def num_vehicles(request):
    return request.param


@pytest.fixture(scope="class")
def factory_parking_lot(
    parking_spot_counts,
    parking_spot_rates_per_sec,
    vehicle_spot_type_mapping,
):
    def _parking_lot(num_spots):
        num_entrance_panels = 2
        num_exit_panels = 2
        num_display_boards = 1
        find_parking_spot_strategy = "nearest"

        return ParkingLot(
            num_entrance_panels,
            num_exit_panels,
            num_display_boards,
            parking_spot_counts(num_spots),
            parking_spot_rates_per_sec,
            vehicle_spot_type_mapping,
            find_parking_spot_strategy,
        )

    return _parking_lot


@pytest.fixture(scope="class")
def factory_vehicles():
    # Factory pattern to create instances of vehicles

    def _vehicles(num_vehicles):
        return [CarFactory().factory_method(vid) for vid in range(num_vehicles)]

    return _vehicles


@pytest.fixture(scope="class")
def parking_lot(num_spots, factory_parking_lot):
    return factory_parking_lot(num_spots)


@pytest.fixture(scope="class")
def vehicles(num_vehicles, factory_vehicles):
    return factory_vehicles(num_vehicles)


@pytest.fixture(scope="class")
def park_vehicles():
    def _park_vehicles(parking_lot: ParkingLot, vehicles: list[Vehicle]):
        def park_one_vehicle(args):
            entrance_panel_id, vehicle = args
            parking_lot.handle_vehicle_entrance(
                entrance_panel_id=entrance_panel_id, vehicle=vehicle
            )

        vehicles_entrance_inputs = []
        for i, vehicle in enumerate(vehicles):
            entrance_panel_id = i % 2
            vehicles_entrance_inputs.append((entrance_panel_id, vehicle))

        with futures.ThreadPoolExecutor() as executor:
            _ = executor.map(park_one_vehicle, vehicles_entrance_inputs)

    return _park_vehicles


@pytest.mark.parametrize("num_vehicles, num_spots", [(1, 1), (2, 2)], indirect=True)
class TestOneVehicleSpotAvailable:
    """Tests:
    1. Ticket issued to vehicle entry with spot available.
    2. Number of free spots reduces by 1.
    """

    def test_vehicle_ticket_issued(self, parking_lot, vehicles, park_vehicles):
        """Unit test to verify vehicle entry when spot is available"""
        park_vehicles(parking_lot, vehicles)
        assert vehicles[0].ticket is not None

    def test_num_free_spots_after_vehicle_entrance(
        self, num_vehicles, num_spots, parking_lot
    ):
        """Unit Test to verify number of free spots is updated after vehicle's entry."""
        spot_type = ParkingSpotType.COMPACT
        assert parking_lot._num_free_spots[spot_type] == num_spots - num_vehicles


@pytest.mark.parametrize("num_vehicles, num_spots", [(1, 0)], indirect=True)
class TestOneVehicleNoSpotAvailable:
    """Test Case: to verify vehicle entry denial if no spot is available"""

    def test_vehicle_entry_denied(self, parking_lot, vehicles, park_vehicles):
        """Unit test to verify vehicle entry is denied when no spot is available"""
        park_vehicles(parking_lot, vehicles)
        assert vehicles[0].ticket is None

    def test_num_free_spots_after_vehicle_entrance(
        self, num_vehicles, num_spots, parking_lot
    ):
        """Unit Test to verify number of free spots is updated after vehicle's entry."""
        spot_type = ParkingSpotType.COMPACT
        assert parking_lot._num_free_spots[spot_type] == num_spots


@pytest.mark.parametrize("num_vehicles, num_spots", [(2, 1)], indirect=True)
class TestTwoVehicleOneSpotAvailable:
    """Test Case: to verify 2 vehicles entry concurrently"""

    def test_vehicle_entry_denied(self, parking_lot, vehicles, park_vehicles):
        """One vehicle should be issued ticket, other should be denied entry"""
        park_vehicles(parking_lot, vehicles)
        assert (vehicles[0].ticket is None and vehicles[1].ticket is not None) or (
            vehicles[1].ticket is None and vehicles[0].ticket is not None
        )

    def test_num_free_spots_after_vehicle_entrance(
        self, num_vehicles, num_spots, parking_lot
    ):
        """Unit Test to verify number of free spots is updated after vehicle's entry."""
        spot_type = ParkingSpotType.COMPACT
        assert parking_lot._num_free_spots[spot_type] == num_spots - (num_vehicles - 1)


@pytest.mark.parametrize("num_vehicles, num_spots", [(2, 2)], indirect=True)
class TestNearestSpotAssigned:
    """Test Case: to verify if nearest spot to entrance is assigned"""

    def test_nearest_spots_assigned(
        self, num_spots, parking_lot, vehicles, park_vehicles
    ):
        """Two vehicles should be issued spots at two ends of spots, closest to entry"""
        park_vehicles(parking_lot, vehicles)
        assert (
            vehicles[0].ticket.spot_id is 0
            and vehicles[1].ticket.spot_id is num_spots - 1
        ) or (
            vehicles[1].ticket.spot_id is 0
            and vehicles[0].ticket.spot_id is num_spots - 1
        )

    def test_num_free_spots_after_vehicle_entrance(
        self, num_vehicles, num_spots, parking_lot
    ):
        """Unit Test to verify number of free spots is updated after vehicle's entry."""
        spot_type = ParkingSpotType.COMPACT
        assert parking_lot._num_free_spots[spot_type] == num_spots - num_vehicles
