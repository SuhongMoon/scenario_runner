
import h5py
import numpy as np
import os

from datetime import datetime

class HDF5Saver:
    def __init__(self, sensor_width, sensor_height, file_path_to_save):
        self.sensor_width = sensor_width
        self.sensor_height = sensor_height

        save_dir = "./_out"

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)            

        current_date_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        file_path_to_save = "{}/{}_{}.hdf5".format(save_dir, file_path_to_save, str(current_date_time))

        self.file = h5py.File(file_path_to_save, "w")
        self.mid_image_dataset = self.file.create_dataset("CameraMiddle", shape=(10, sensor_height, sensor_width, 3), maxshape=(None, sensor_height, sensor_width, 3), dtype='i2')
        self.right_image_dataset = self.file.create_dataset("CameraRight", shape=(10, sensor_height, sensor_width, 3), maxshape=(None, sensor_height, sensor_width, 3), dtype='i2')
        self.left_image_dataset = self.file.create_dataset("CameraLeft", shape=(10, sensor_height, sensor_width, 3), maxshape=(None, sensor_height, sensor_width, 3), dtype='i2')

        self.labels_list = [
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

        self.labels_dataset_dict = dict()
        for label in self.labels_list:
            if label in ["acceleartion", "velocity", "location", "rotation"]:
                self.labels_dataset_dict[label] = self.file.create_dataset(label, shape=(10, 3), maxshape=(None,3), dtype='f')
            else:
                self.labels_dataset_dict[label] = self.file.create_dataset(label, shape=(10, 1), maxshape=(None,1), dtype='f')

        # Storing metadata
        self.file.attrs['sensor_width'] = sensor_width
        self.file.attrs['sensor_height'] = sensor_height
        self.file.attrs['simulation_synchronization_type'] = "syncd"
        self.file.attrs['channels'] = "RGB"
        self.file.attrs['fps'] = 10

        self.idx = 0
        self.max_size = 10

    def record_data(self, middle_image, right_image, left_image, labels):
        if self.idx >= self.max_size:
            self.max_size += 1

            self.mid_image_dataset.resize(self.max_size, 0)
            self.right_image_dataset.resize(self.max_size, 0)
            self.left_image_dataset.resize(self.max_size, 0)

            for label in self.labels_list:
                self.labels_dataset_dict[label].resize(self.max_size, 0)
        
        self.mid_image_dataset[self.idx] = middle_image
        self.right_image_dataset[self.idx] = right_image
        self.left_image_dataset[self.idx] = left_image

        for label in self.labels_list:
            self.labels_dataset_dict[label][self.idx] = labels[label]
        
        self.idx += 1

    def close_HDF5(self):
        self.file.close()