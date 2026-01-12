from PIL import Image, ImageFilter

def denoise_image(img: Image.Image, strength: float = 1.0) -> Image.Image:
    radius = max(0.0, min(float(strength), 5.0))
    if radius <= 0.0:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=radius))
