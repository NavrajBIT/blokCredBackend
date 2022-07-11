from django.conf import settings
import os

# Importing the PIL library
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def create_image(myname): 
    # Open an Image
    image_filepath = os.path.join(settings.BASE_DIR, "api/template.jpeg")
    img = Image.open(image_filepath)
    
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img)

    # Custom font style and font size
    myFont = ImageFont.truetype('arial.ttf', 65)
    
    # Add Text to an image
    I1.text((400, 450), myname, font=myFont, fill=(255, 0, 0))
    
    # Display edited image
    img.show()
    
    # Save the edited image
    img.save("api/certificate.png")
    return img