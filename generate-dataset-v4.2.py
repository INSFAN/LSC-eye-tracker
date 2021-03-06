# -*- coding: utf-8 -*-
'''
    Author: Wenyu
    Date: 2/11/2019
    Version: 4.1
    
    Function:
    v4.0: This script tries to process MPIIFaceGaze data into npz
    Then for our model test
    v4.1: use function to structured
    v4.2: Generate data for each person
'''
import numpy as np
import cv2
import time
import os
import sys
from scipy.io import loadmat

# TODO: license required

# this code generate the whole dataset .npz file from the original images
# in folder 'image' with 'gazeData.txt', resize images to 224 * 224

# TODO: a dataset info field should be added and save in the file as one field

DATASET_ROOT = ''

def load_mat(path):
    m = loadmat(path)
    print ("Screen height: {}".format(m['height_pixel']))
    print ("Screen width: {}".format(m['width_pixel']))
    return m['height_pixel'], m['width_pixel']


def generate_gaze_tensor(gaze_point, width, height, scale):
    '''
        generate gaze tensor from gaze point
    '''
    w = int(gaze_point[0])
    h = int(gaze_point[1])
    c = 1.0 / scale
    gaze_tensor = np.zeros([scale, scale, 3], dtype='float32')
    for m in range(scale):
        for n in range(scale):
            x = (c / 2 + c * m) * width
            y = (c / 2 + c * n) * height
            # the distance from the gaze point to the point of each cell predicts
            dis = np.sqrt((x - w) * (x - w) + (y - h) * (y - h))
            gaze_tensor[m, n, :] = [(w - x) / width,
                                    (h - y) / height,
                                    1.0 / (dis + 1.0)]
    return gaze_tensor

def main():
    """
        main function
        argv[1]: dataset root folder
    """

    # change current dir to dataset folder
    dataset_folder = sys.argv[1]
    # Warning
    print('################################################################')
    print('# WARNING: The Code Should Be Tested On A Small Dataset First! #')
    print('#            THIS code should run in dataset folder!           #')
    print('################################################################')

    face_size = 224
    for person in os.listdir(dataset_folder):
        save_name = 'data_MPIIFaceGaze_'+person+'_test.npz'
        path_to_mat_file = os.path.abspath(os.path.join(dataset_folder, person+'/Calibration/screenSize.mat'))
        # The width and height values are recorded in the calibration data .mat
        height, width = load_mat(path_to_mat_file)

        # Change current dir to person dir
        os.chdir(os.path.abspath(os.path.join(dataset_folder, person)))
        file_name = person + '.txt'
        amount = 0
        for index, line in enumerate(open(file_name,'r')):
            amount += 1 
        print("person {} amount = {}".format(person, amount))

        # we use 'uint8' to reduce file size for storage, but require 'float32'
        # when computing on GPU
        face_data = np.zeros([amount, face_size, face_size, 3], dtype='uint8')
        # this generates a mapping tensor for regression from the original
        # tensor region size
        scale = 7
        # dim-4 indicates (x, y, p) 
        eye_track_data = np.zeros([amount, scale, scale, 3], dtype='float32')

        t_start = time.time()

        index = 0

        with open(file_name, 'r') as file:
            for line in file.readlines():
                vector = line.split(' ')
                # print(vector[0], vector[1], vector[2])
                image_src = cv2.imread(vector[0])
                # cv2.imshow('test', image_src)
                # cv2.waitKey(0)
                # TODO: according to YOLO v1, HSV color space need to be tested
                image_dst = cv2.resize(image_src, (face_size, face_size))

                face_data[index, :, :, :] = image_dst
                # TODO: according to YOLO v2, they used logistic activation to normalize
                # maybe [0, 1] is better than [-0.5, 0.5] according to Relu
                eye_track_data[index, :, :, :] = generate_gaze_tensor(vector[1:3],
                                                                    width,
                                                                    height,
                                                                    scale)

                print('No. {} {}'.format(index, vector[:3]))
                index += 1
          
        # TODO: a data info field should be saved within   
        # .npz file was saved in data folder     
        np.savez_compressed(save_name,
                            faceData=face_data,
                            eyeTrackData=eye_track_data)

        print(time.time() - t_start)

if __name__ == '__main__':
    main()
