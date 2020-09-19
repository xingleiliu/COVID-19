#!/usr/bin/env python

import json
import os
import argparse
import numpy as np
import cv2
import torch
import glob
from PIL import Image


from Tools.database_iterator_30kcams import database_iterator
from Tools.scene_detection_30kcams import SceneDetectionClass
from Pedestron.mmdet.apis import init_detector, inference_detector


def determine_day_night(image):  # determines whether or not an image is captured during the day or night
    # 0 denotes night, 1 denotes day
    if np.mean(image) > 60:
        # this image was taken during the day
        return 1
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run person detections on all videos')
    parser.add_argument('--config', help='test config file path', default='Pedestron/configs/elephant/cityperson/cascade_hrnet.py')
    parser.add_argument('--checkpoint', help='checkpoint file', default='Pedestron/models_pretrained/epoch_19.pth.stu')
    parser.add_argument('--path', help = 'path to videos', default='/projects/SE_HPC/video_frames/')
    parser.add_argument('--start_index', required=True, type=int)
    parser.add_argument('--end_index', required=True, type=int)
    args = parser.parse_args()
    
    beach_file = open('done_vidcams.txt', 'r')
    lines = beach_file.read().split('\n')
    beaches = lines
    print(beaches)

    model = init_detector(
        args.config, args.checkpoint, device=torch.device('cuda:0'))

    path = args.path

    count = 0

    list_cams = os.listdir(path)

    
    list_cams = [k + '/' for k in list_cams]
    text_file = open('done.txt', 'r')
    lines = text_file.read().split('\n')
    done = lines
    if done == None:
        done = []
    text_file.close()
   
    detections = dict()
    day_night = dict()
    start_index = args.start_index
    end_index = args.end_index

    downloaded_beach_cams = [i for i in list_cams if i not in beaches]
    print(len(downloaded_beach_cams))
    for cam in downloaded_beach_cams[start_index:end_index]:
        #if cam not in done:
        count+=1
        print(count)
        detections[cam] = dict()
        day_night[cam] = dict()

        for date in os.listdir(path + cam):
            print(date)
            detections[cam][date] = dict()
            day_night[cam][date] = dict()

            for image in os.listdir(path + cam + date):
                #print(path + cam + date + '/' + image)
                detections[cam][date][image] = dict()
                day_night[cam][date][image] = dict()
                try:
                    pil_image = Image.open(path + cam + date + '/' + image)
                    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    # day night calculation
                    if determine_day_night(img) == 0:
                        day_night[cam][date][image] = 'night'
                    else:
                        day_night[cam][date][image] = 'day'
			   
                    results = inference_detector(model, img)
                    if isinstance(results, tuple):
                        bbox_result, segm_result = results
                    else:
                        bbox_result, segm_result = results, None
                    bboxes = np.vstack(bbox_result)
                    bboxes = bboxes.tolist()
                    bbox_dict = dict()
                    for each in bboxes:
                        bbox_dict[each[4]] = each[0:4]
		
                    detections[cam][date][image] = bbox_dict
                except:
                    continue
        f = open('done.txt', 'a')
        f.write(cam + '/n')
        f.close()

        f = open("person_detections_new_video_all_" + str(start_index) + "_" + str(end_index), "w+")
        f.write(json.dumps(detections))
        f.close()

        f = open("day_night_video_new_detections_all" + str(start_index) + "_" + str(end_index), "w+")
        f.write(json.dumps(day_night))
        f.close()
        
