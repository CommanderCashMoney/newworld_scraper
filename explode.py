from PIL import Image

folder = "images/spinner"
im = Image.open("images/spinner.png")

new_size = 25
im2 = im.resize((int(im.width / 144 * new_size), int(im.height / 144 * new_size)))
print(im2.width, im2.height)

tot = 0
for y in range(0, im2.height, new_size):
    for x in range(0, im2.width, new_size):
        crop = (x, y, x+new_size, y+new_size)
        print(crop)
        im3 = im2.crop(crop)
        im3.save(f"{folder}/{tot}.png")
        tot += 1