import h5py
import cv2
import numpy as np
import sys
import carla
import queue

from carla import ColorConverter as cc


labels_list = [
            "acceleartion", 
            "velocity", 
            "speed", 
            "location", 
            "rotation",
            "brake",
            "gear",
            "hand_brake",
            "manual_gear_shift",
            "reverse",
            "steer",
            "throttle"
        ]

def image2numpy(image):
    image.convert(cc.Raw)
    array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    array = np.reshape(array, (image.height, image.width, 4))
    array = array[:, :, :3]
    array = array[:, :, ::-1]

    return array 

def to_numpy(vector):
    if isinstance(vector, carla.Vector3D):
        return np.array([vector.x, vector.y, vector.z])
    elif isinstance(vector, carla.Rotation):
        return np.array([vector.pitch, vector.yaw, vector.roll])


def get_labels(world):
    compass = np.array([world.imu_sensor.compass], dtype=np.float64)
    gps_data = np.array([world.gnss_sensor.lat, world.gnss_sensor.lon], dtype=np.float64)
    acceleartion = np.array(world.imu_sensor.accelerometer, dtype=np.float64) # m/s^2

    player = world.player
    velocity = to_numpy(player.get_velocity()) # m/s
    speed = np.sqrt((velocity**2).sum()) # m/s
    transform = player.get_transform()
    location = to_numpy(transform.location) # m
    rotation = to_numpy(transform.rotation) # degrees

    control = player.get_control()
    brake = control.brake
    gear = control.gear
    hand_brake = control.hand_brake
    manual_gear_shift = control.manual_gear_shift
    reverse = control.reverse
    steer = control.steer
    throttle = control.throttle

    labels_dict = dict(
        compass=compass,
        gps_data=gps_data,
        acceleartion=acceleartion,
        velocity=velocity,
        speed=speed,
        location=location,
        rotation=rotation,
        brake=brake,
        gear=gear,
        hand_brake=hand_brake,
        manual_gear_shift=manual_gear_shift,
        reverse=reverse,
        steer=steer,
        throttle=throttle
    )

    return labels_dict

class CarlaSyncMode(object):
    """
    Context manager to synchronize output from different sensors. Synchronous
    mode is enabled as long as we are inside this context
        with CarlaSyncMode(world, sensors) as sync_mode:
            while True:
                data = sync_mode.tick(timeout=1.0)
    """

    def __init__(self, world, *sensors, **kwargs):
        self.world = world
        self.sensors = sensors
        self.frame = None
        self.delta_seconds = 1.0 / kwargs.get('fps', 20)
        self._queues = []
        self._settings = None

    def __enter__(self):
        self._settings = self.world.get_settings()
        self.frame = self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False,
            synchronous_mode=True,
            fixed_delta_seconds=self.delta_seconds))

        def make_queue(register_event):
            q = queue.Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self.world.on_tick)
        for sensor in self.sensors:
            make_queue(sensor.listen)
        return self

    def tick(self, timeout):
        self.frame = self.world.tick()
        data = [self._retrieve_data(q, None) for q in self._queues]
        assert all(x.frame == self.frame for x in data)
        return data

    def __exit__(self, *args, **kwargs):
        self.world.apply_settings(self._settings)

    def _retrieve_data(self, sensor_queue, timeout):
        while True:
            data = sensor_queue.get(timeout=timeout)
            if data.frame == self.frame:
                return data

def generate_rgb_cam(world, cam_transform, attach_to, height=144, width=256, fov=90):
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', str(width))
    camera_bp.set_attribute('image_size_y', str(height))
    camera_bp.set_attribute('fov', str(fov))
    camera_rgb = world.spawn_actor(
            camera_bp,
            cam_transform[0],
            attach_to=attach_to,
            attachment_type = cam_transform[1])

    return camera_rgb
