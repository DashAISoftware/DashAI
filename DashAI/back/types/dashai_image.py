from dataclasses import dataclass

from datasets import Image


@dataclass
class DashAIImage(Image):
    """Wrapper dataclass to represent Images

    DashAIImage feature can represent:
    - A `str`: Absolute path to the image file (i.e. random access is allowed).
    - A `dict` with the keys:

        - `path`: String with relative path of the image
        file to the archive file.
        - `bytes`: Bytes of the image file.

      This is useful for archived files with sequential access.

    - An `np.ndarray`: NumPy array representing an image.
    - A `PIL.Image.Image`: PIL image object.

    Attributes
    ----------
        mode (`str`, *optional*):
            The mode to convert the image to. If `None`,
            the native mode of the image is used.
        decode (`bool`, defaults to `True`):
            Whether to decode the image data. If `False`,
            returns the underlying dictionary in the format
            `{"path": image_path, "bytes": image_bytes}`.

    Parameters
    Image : _type_
        _description_
    """
