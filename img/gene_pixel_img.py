from PIL import Image
import random

# 16进制颜色格式颜色转换为RGB格式


def Hex_to_RGB(hex):
    r = int(hex[1:3], 16)
    g = int(hex[3:5], 16)
    b = int(hex[5:7], 16)
    # rgb = str(r)+','+str(g)+','+str(b)
    rgb = (r, g, b)
    # print(rgb)
    return rgb


x = 20
y = 20

c = Image.new("RGB", (x, y))

# for i in range(0, 40):
#     for j in range(0, 40):
#         c.putpixel([i, j], (random.randint(0, 255),
#                    random.randint(0, 255), random.randint(0, 255)))


worker_addrs = [
    "9.5,0;9,1;8,3,1,2;7,5,1,2;6,7,1,2;7,10,2;9,9",
    "9,2,2,7;8,5,4,2;7,7,6,2;6,9,1,3;13,9,1,3;10,9;9,10,4,3;7,11,2,2;9,13,2",
    "10,1;11,3,1,2;12,5,1,2;13,7,1,2;8,13;11,13;9,14,2;9.5,15",
    "5,9;4,10;3,11;2,12;1,13",
    "5,10;4,11,2;3,12,3;14,10;14,11,2;14,12,3",
    "2,13,3;14,9;15,10;16,11;17,12;15,13,4",
    "9.5,6;9,7,2;8,8,4;7,9,2;11,9,2;6,12;5,13,3;4,14,5;13,12;12,13,3;11,14,5",
]


workers_colors = ["#F1E61D", "#E2CD13", "#C0AE10",
                "#AA990E", "#716609", "#FF0000", "#00FF00"]
for index in range(len(workers_colors)):
    worker_rgb = Hex_to_RGB(workers_colors[index])
    # print("ff", worker_rgb)
    worker_addr = worker_addrs[index]
    pixel_list = worker_addr.split(';')
    # print("lsit", pixel_list)
    for pixel in pixel_list:
        pixel_coord = pixel.split(',')
        pixel_coord = [int(float(x)) for x in pixel_coord]
        print(pixel_coord)
        c.putpixel(pixel_coord[:2], worker_rgb)

c.show()
c.save("c.png")
