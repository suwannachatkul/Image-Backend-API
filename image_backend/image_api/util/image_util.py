import logging
import os
from io import BytesIO
from typing import Union

import PIL.Image

# Suppress PIL logging
logging.getLogger("PIL.Image").setLevel(logging.CRITICAL + 1)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL + 1)


DEFAULT_TARGET_SIZE = 1 * 1024 * 1024
DEFAULT_MAX_DIMENSION = 2400


class ImageUtil:

    @staticmethod
    def open_image(image: Union[os.PathLike, str, bytes, BytesIO, PIL.Image.Image]) -> PIL.Image.Image:
        """
        Open the image using various input types.

        Args:
            image (Union[os.PathLike, str, bytes, BytesIO, Image.Image]): The input image data.

        Returns:
            Image.Image: The opened image.

        Raises:
            OSError: If the image cannot be opened or converted.
            ValueError: If the input image type is not supported.
        """
        if isinstance(image, (os.PathLike, str, BytesIO)):
            return PIL.Image.open(image)
        elif isinstance(image, bytes):
            return PIL.Image.open(BytesIO(image))
        elif isinstance(image, PIL.Image.Image):
            return image
        else:
            raise ValueError(f"Unsupported image type. {type(image)}")

    @staticmethod
    def PIL_to_bytes(image: PIL.Image.Image, file_ext: str) -> BytesIO:
        """
        Convert a PIL image to bytes.

        Args:
            image (Image.Image): The PIL image to convert.
            file_ext (str): The file extension of the output image.

        Returns:
            BytesIO: The converted image as bytes.

        """
        output = BytesIO()
        image.save(output, format=file_ext.upper(), quality=90)
        output.seek(0)
        return output

    @classmethod
    def convert_image_type(cls, image: Union[os.PathLike, str, bytes, BytesIO, PIL.Image.Image],
                           file_ext: str) -> PIL.Image.Image:
        """
        Convert the image to the specified file format.

        Args:
            image (Union[os.PathLike, str, bytes, BytesIO, PIL.Image.Image]): The input image data.
            file_ext (str): The desired file extension for the output image.

        Returns:
            Image.Image: The converted image.

        """
        img = cls.open_image(image)

        # jpg is jpeg in PIL
        if file_ext == 'jpg':
            file_ext = 'jpeg'

        # Convert to file_ext if not already
        if img.format != file_ext.upper():
            img = img.convert('RGBA' if file_ext.lower() == 'png' else 'RGB')
            img.format = file_ext.upper()

        return img

    @classmethod
    def reduce_image_size(cls,
                          image: Union[os.PathLike, str, bytes, BytesIO, PIL.Image.Image],
                          max_dimension: int = DEFAULT_MAX_DIMENSION) -> PIL.Image.Image:
        """
        Reduce the size of the image while maintaining aspect ratio.

        Args:
            image (Union[os.PathLike, str, bytes, BytesIO, PIL.Image.Image]): The input image data.
            max_dimension (int): The maximum dimension (width or height in pixels) of the output image.

        Returns:
            Image.Image: The resized image.

        """
        img = cls.open_image(image)
        width, height = img.size

        # If the image size is already smaller than the max_dimension size, return the original image
        if max(width, height) <= max_dimension:
            return img

        # if half size still more than max_dimension, set it to max_dimension with keeping image ratio
        # else just resize to half size
        if max(width, height) / 2 > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int((new_width / width) * height)
            else:
                new_height = max_dimension
                new_width = int((new_height / height) * width)
        else:
            new_width = width // 2
            new_height = height // 2

        resized_img = img.resize((new_width, new_height))
        return resized_img

    @classmethod
    def optimize_image_bytes_size(cls,
                                  image: bytes,
                                  file_ext: str = 'jpeg',
                                  target_size: int = DEFAULT_TARGET_SIZE) -> BytesIO:
        """
        Optimize the size of the bytes image (Ex. image data from InMemoryUploadedFile) .

        Args:
            image (bytes): The input image data as bytes.
            file_ext (str): The desired file extension for the output image.
            target_size (int): The target size of the output image in bytes.

        Returns:
            BytesIO: The optimized image as BytesIO.

        """
        if file_ext == 'jpg':
            file_ext = 'jpeg'

        img = cls.convert_image_type(image, file_ext)

        # Save the resized image to a BytesIO object
        output = BytesIO()
        img.save(output, format=file_ext.upper(), quality=90)

        # Get the file size
        file_size = output.tell()

        # If the file size is still greater than the target size, resize the image
        if file_size > target_size:
            resized_img = cls.reduce_image_size(img)

            output = BytesIO()
            resized_img.save(output, format=file_ext.upper(), quality=90)

        # Reset the file pointer to the beginning of the stream
        output.seek(0)

        return output
