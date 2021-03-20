#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

"""
Welcome to CARLA manual control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    A/D          : steer left/right
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down
    CTRL + W     : toggle constant velocity mode at 60 km/h


    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    H/?          : toggle help
    ESC          : quit
"""

from __future__ import print_function

# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================


import carla

from utils.manual_control_utils import World, HUD, KeyboardControl, CameraManager, CollisionSensor, LaneInvasionSensor, GnssSensor, IMUSensor
from utils.sensor_utils import CarlaSyncMode, get_labels, parsing_data
from utils.data_saver_utils import HDF5Saver

import os
import argparse
import logging
import time
import pygame

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================

class WorldSR(World):

    restarted = False

    def restart(self):

        if self.restarted:
            return
        self.restarted = True

        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713

        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0

        # Get the ego vehicle
        while self.player is None:
            print("Waiting for the ego vehicle...")
            time.sleep(1)
            possible_vehicles = self.world.get_actors().filter('vehicle.*')
            for vehicle in possible_vehicles:
                if vehicle.attributes['role_name'] == "hero":
                    print("Ego vehicle found")
                    self.player = vehicle
                    break
        
        self.player_name = self.player.type_id

        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.imu_sensor = IMUSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def tick(self, clock):
        if len(self.world.get_actors().filter(self.player_name)) < 1:
            return False

        self.hud.tick(self, clock)
        return True

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

import matplotlib.pyplot as plt

def game_loop(args):
    pygame.init()
    pygame.font.init()

    world = None
    record_cameras = []

    data_saver = None#HDF5Saver(args.cam_width, args.cam_height, args.save_name)

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height)
        # world = WorldSR(client.get_world(), hud, args) 
        world = World(client.get_world(), hud, args) # Debugging
        controller = KeyboardControl(world, args.autopilot)
        clock = pygame.time.Clock()

        with CarlaSyncMode(world.world,  *[], fps=10) as sync_mode:
            while True:
                clock.tick_busy_loop(60)
                if controller.parse_events(client, world, clock):
                    return
                world.tick(clock)
                world.render(display)
                sync_mode.tick(1.0)
                pygame.display.flip()

                center_img = world.camera_manager.data_cam_images['rgb']
                right_img = world.camera_manager.data_cam_images['rgb_right']
                left_img = world.camera_manager.data_cam_images['rgb_left']

                print(center_img.shape)
                print(right_img.shape)
                print(left_img.shape)

                if world.camera_manager.recording:
                    if data_saver is None:
                        data_saver = HDF5Saver(args.cam_width, args.cam_height, args.save_name)

                    labels_dict = get_labels(world)
                    center_img = world.camera_manager.data_cam_images['rgb']
                    right_img = world.camera_manager.data_cam_images['rgb_right']
                    left_img = world.camera_manager.data_cam_images['rgb_left']

                    print(center_img.shape)
                    print(right_img.shape)
                    print(left_img.shape)
                
                else:
                    if data_saver is not None:
                        data_saver.close_HDF5()
                    data_saver = None

    finally:
        
        if (world and world.recording_enabled):
            client.stop_recorder()

        if world is not None:
            world.destroy()
        
        if len(record_cameras) > 0:
            for camera in record_cameras:
                camera.destroy()
        
        if data_saver is not None:
            data_saver.close_HDF5()

        world.world.apply_settings(carla.WorldSettings(synchronous_mode=False))
        # syn
        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--save-name', 
        default=None, 
        type=str, 
        help="Name of h5 file to save the data"
    )
    argparser.add_argument(
        '-wi', '--cam_width', 
        default=640, 
        type=int, 
        help="recording camera rgb sensor width in pixels"
    )
    argparser.add_argument(
        '-he', '--cam_height', 
        default=480, 
        type=int, 
        help="recording camera rgb sensor width in pixels"
    )
    argparser.add_argument(
        '--style', 
        default="aggressive", 
        type=str, 
        choices=['aggressive', 'cautious'],
        help="Driving style (aggressive, cautious)"
    )
    args = argparser.parse_args()

    args.rolename = 'hero'      # Needed for CARLA version
    args.filter = "vehicle.*"   # Needed for CARLA version
    args.gamma = 2.2   # Needed for CARLA version
    args.width, args.height = [int(x) for x in args.res.split('x')]

    if args.save_name is None:
        args.save_name = args.style
    else:
        args.save_name = "{}_{}".format(args.style, args.save_name)

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:

        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    except Exception as error:
        logging.exception(error)


if __name__ == '__main__':

    main()
