"""Module: Parking Lot Application."""
import logging.config
import time
from concurrent import futures
from pathlib import Path
from threading import Thread

import typer
import yaml
# from account import AccountStatus, Admin, Person
from panel import EntrancePanel, ExitPanel
from parking_lot import ParkingLot
from parking_spot import ParkingSpotType
from typing_extensions import Annotated
from vehicle import Car, Vehicle, VehicleType

app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command()
def parking_lot_app(
    num_entrance_panels: Annotated[
        int, typer.Argument(help="Number of entrance panels")
    ] = 2,
    num_exit_panels: Annotated[
        int, typer.Argument(help="Number of entrance panels")
    ] = 2,
    num_display_boards: Annotated[
        int, typer.Argument(help="Number of dispaly boards")
    ] = 1,
    find_parking_spot_strategy: Annotated[
        str,
        typer.Argument(
            help="first: Find first free spot, nearest: Find nearest free spot to entrance"
        ),
    ] = "nearest",
):
    """
    Initialize parking lot app.

    Args:
        num_entrance_panels (int): Number of entrance panels
        num_exit_panels (int): Number of exit panels
    """

    parking_spot_counts = {
        ParkingSpotType.MOTORBIKE: 50,
        ParkingSpotType.COMPACT: 25,
        ParkingSpotType.LARGE: 15,
        ParkingSpotType.HANDICAPPED: 5,
    }

    parking_spot_rates_per_sec = {
        ParkingSpotType.MOTORBIKE: 0.0025,
        ParkingSpotType.COMPACT: 0.005,
        ParkingSpotType.LARGE: 0.01,
        ParkingSpotType.HANDICAPPED: 0.002,
    }

    vehicle_spot_type_mapping = {
        VehicleType.CAR: ParkingSpotType.COMPACT,
        VehicleType.TRUCK: ParkingSpotType.LARGE,
        VehicleType.MOTORBIKE: ParkingSpotType.MOTORBIKE,
    }

    # Create singleton instance of Parking Lot
    parking_lot = ParkingLot(
        num_entrance_panels,
        num_exit_panels,
        num_display_boards,
        parking_spot_counts,
        parking_spot_rates_per_sec,
        vehicle_spot_type_mapping,
        find_parking_spot_strategy,
    )

    # Create vehicles
    car1 = Car(vehicle_id=1)
    car2 = Car(vehicle_id=2)

    def park_one_vehicle(args):
        entrance_panel_id, vehicle = args
        vehicle_id = vehicle.vehicle_id
        vechicle_type = vehicle.vehicle_type
        logger.info(
            f" Vehicle of type: {vechicle_type} with ID: {vehicle_id} arrived at entrance panel with id: {entrance_panel_id} "
        )
        parking_lot.handle_vehicle_entrance(
            entrance_panel_id=entrance_panel_id, vehicle=vehicle
        )

    def exit_one_vehicle(args):
        exit_panel_id, vehicle = args
        vehicle_id = vehicle.vehicle_id
        vechicle_type = vehicle.vehicle_type
        logger.info(
            f" Vehicle of type: {vechicle_type} with ID: {vehicle_id} exiting at exit panel with id: {exit_panel_id} "
        )
        parking_lot.handle_vehicle_exit(exit_panel_id=exit_panel_id, vehicle=vehicle)

    with futures.ThreadPoolExecutor() as executor:
        _ = executor.map(park_one_vehicle, [(0, car1), (1, car2)])
        time.sleep(3)
        _ = executor.map(exit_one_vehicle, [(0, car1), (1, car2)])


if __name__ == "__main__":
    app()
