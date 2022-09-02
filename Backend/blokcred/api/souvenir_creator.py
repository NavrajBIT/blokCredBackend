from django.conf import settings
import os
import urllib.request
import random
import ssl

# Importing the PIL library
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def add_souvenir_frame(base_image, frame_url): 
    filename = frame_url.split("/")[-1]
    print(filename)
    print("Frame url ------------------------------------------" + frame_url)
    urllib.request.urlretrieve(frame_url, filename)    
    frame_image = Image.open(filename)
    base_image = Image.open(base_image)

    frame_image = frame_image.resize((1920, 1080))
    base_image = base_image.resize((1920, 1080))

    base_image.paste(frame_image, (0, 0), frame_image)

    
    
    # Call draw Method to add 2D graphics in an image
    # frame = ImageDraw.Draw(frame_image)
    # base = ImageDraw.Draw(base_image) 
    # Display edited image
    # frame_image.show()
    base_image.show()
    
    # Save the edited image
    filepath = "api/souvenir" + str(random.randrange(1, 10000, 1)) + ".png"
    print(filepath)    
    base_image.save(filepath)
    return filepath