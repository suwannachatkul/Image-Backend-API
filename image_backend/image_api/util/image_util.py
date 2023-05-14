import os
from io import BytesIO

import PIL.Image


class ImageUtil:
    
    @staticmethod
    def optimize_imgsize(image):
        # Read the contents of the file into a BytesIO object
        file = BytesIO(image.read())

        img = PIL.Image.open(file)

        # Convert to JPEG if not already
        if img.format != 'JPEG':
            img = img.convert('RGB')
        
        # Save the resized image to a BytesIO object
        output = BytesIO()
        img.save(output, format='JPEG', quality=90)

        # Get the file size
        file_size = output.tell()

        # If the file size is still greater than 1MB, resize in half or 2400px
        if file_size > 1 * 1024 * 1024:
            width, height = img.size
            # if half value still more than 2400 set it to 2400px with keeping image ratio
            if max(width, height) / 2 > 2400:
                if width > height:
                    new_width = 2400
                    new_height = int((new_width / width) * height)
                else:
                    new_height = 2400
                    new_width = int((new_height / height) * width)
            else:
                new_width = width // 2
                new_height = height // 2
            resized_img = img.resize((new_width, new_height))

            output = BytesIO()
            resized_img.save(output, format='JPEG', quality=90)

            file_size2 = output.tell()

        # Reset the file pointer to the beginning of the stream
        output.seek(0)

        # Return the resized image
        return output