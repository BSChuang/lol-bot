import requests
import cv2
import glob
from PIL import Image
import configparser
import os
import pathlib
import shutil
import hikari

config = configparser.ConfigParser()
config.read("config.ini")

BASE_URL = 'https://bschuang-modelscope-text-to-video-synthesis.hf.space'
BEARER = config['discord']['hf_token']
FPS = 8

def get_gif(prompt):
    try:
        response = requests.post(f"{BASE_URL}/run/predict", headers={
            "Authorization": f"Bearer {BEARER}"
        }, json={
            "data": [
                prompt,
            ]
        })

        video_path = response.json()['data'][0]['name']

        response = requests.get(f"{BASE_URL}/file={video_path}", headers={
            "Authorization": f"Bearer {BEARER}"
        })
        f=open("temp.mp4", 'wb')
        for chunk in response.iter_content(chunk_size=255): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
        f.close()

        convert_mp4_to_jpgs("./temp.mp4")
        os.remove('./temp.mp4')
        make_gif("output")
        shutil.rmtree(pathlib.Path('./output'))

        f = hikari.File('./temp.gif')
        return f
    except Exception as e:
        print(e)
        return e


def convert_mp4_to_jpgs(path):
    video_capture = cv2.VideoCapture(path)
    still_reading, image = video_capture.read()
    frame_count = 0
    os.mkdir('output')
    while still_reading:
        cv2.imwrite(f"./output/frame_{frame_count:03d}.jpg", image)
        
        # read next image
        still_reading, image = video_capture.read()
        frame_count += 1


def make_gif(frame_folder):
    images = glob.glob(f"{frame_folder}/*.jpg")
    images.sort()
    frames = [Image.open(image) for image in images]
    frame_one = frames[0]
    frame_one.save("temp.gif", format="GIF", append_images=frames,
                   save_all=True, duration=FPS, loop=0)
    
if __name__ == "__main__":
    get_gif("times square at night.")
    # convert_mp4_to_jpgs("./temp.mp4")