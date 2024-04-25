import requests
import cv2
import glob
from PIL import Image
import configparser
import os
import urllib
import discord

config = configparser.ConfigParser()
config.read("config.ini")

BASE_URL = 'https://bschuang-modelscope-text-to-video-synthesis.hf.space'
BEARER = config['discord']['hf_token']
FPS = 156


def get_media(prompt):
    try:
        data = None
        response = requests.post(
            f"{BASE_URL}/run/predict_1", 
            timeout=720,
            headers={
                "Authorization": f"Bearer {BEARER}"
            }, 
            json={
                "data": [
                    prompt,
                ]
            },
        )

        if response.status_code == 200:
            data = response.json()['data'][0]

        if data == None:
            return "Failed to generate."
        
        image = urllib.request.urlopen(data)
        with open('temp.png', 'wb') as f:
            f.write(image.file.read())
        result = discord.File('temp.png')
        
        return result
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
    # get_gif("times square at night.")
    get_media("a squirrel", 'predict_1')
    # convert_mp4_to_jpgs("./temp.mp4")