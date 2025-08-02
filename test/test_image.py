import cv2

image_path = 'data/known_faces/customer1/img1.jpg'
image = cv2.imread(image_path)
if image is None:
    print("Image load failed! Check the file path or format.")
else:
    print("Image loaded successfully!")
    print(f"Image shape: {image.shape}")