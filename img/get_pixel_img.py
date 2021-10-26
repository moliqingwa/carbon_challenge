from PIL import Image
# import cv2

# 将颜色RGB转换为十六进制
def RGB_to_Hex(rgb):
    # RGB = rgb.split(',')            # 将RGB格式划分开来
    color = '#'
    for i in rgb:
        num = int(i)
        # 将R、G、B分别转化为16进制拼接转换并大写  hex() 函数用于将10进制整数转换成16进制，以字符串形式表示
        color += str(hex(num))[-2:].replace('x', '0').upper()
    # print(color)
    return color

# filename = './img/person.jpg'
# image=cv2.imread(filename)
# src_strlist=cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
# print("img4", src_strlist[30])


# ----------存在有多个相邻点相似值问题
# 打开要处理的图像
image = Image.open('./img/person.png')

# 图片重塑为正方形
w, h = image.size
background = Image.new('RGBA', size=(max(w, h), max(w, h)), color=(0, 0, 0, 0))
length = int(abs(w - h) // 2)  # 一侧需要填充的长度
box = (length, 0) if w < h else (0, length)  # 粘贴的位置
background.paste(image, box)

# 转换图片的模式为RGBA
image = image.convert('RGBA')
print("heti", image.height, image.width)
# image.show()
# 获得文字图片的每个像素点
src_strlist = image.load()

# 获取所有种类颜色
colors = []
pixel = []

# 创建dict存储颜色及其对应坐标点
color_pixel = {}

# # 按单个像素点绘制
# for x in range(0, 41):
#     for y in range(0, 40):
#         data = src_strlist[x, y]        # RGBA颜色
#         hex_data = RGB_to_Hex(data)     # 十六进制颜色

#         if(data[3] == 0):               # 透明色时跳过循环
#             continue
#         if(hex_data not in colors):         # 非透明色时记录颜色到colors数组
#             colors.append(hex_data)
#             color_pixel[hex_data] = []
#         color_pixel[hex_data].append(str(x)+','+str(y))


# for key in color_pixel:
#     pixel.append(';'.join(color_pixel[key]))

# print(colors)
# print(pixel)

# 多个横向坐标拼接
for x in range(0, 49):
    for y in range(0, 40):
        data = src_strlist[x, y]        # RGBA颜色
        hex_data = RGB_to_Hex(data)     # 十六进制颜色

        if(data[3] == 0):               # 透明色时跳过循环
            continue
        if(hex_data not in colors):         # 非透明色时记录颜色到colors数组
            colors.append(hex_data)
            color_pixel[hex_data] = []
        color_pixel[hex_data].append( (x,y) )

print(color_pixel)
for key in color_pixel:  
    # print(color_pixel[key])   # 某一种颜色的所有像素坐标数组
    x_len = 1
    cur_coord = ()  # 起始坐标位置
    pre_coord = ()  # 上一个坐标点位置
    for coord in color_pixel[key]:
        if(not pre_coord):  # 说明该坐标是第一个
            cur_coord = coord      # 记录坐标起始点
            pre_coord = coord
            # continue
        else:
            # print("1231", pre_coord, coord)
            if(coord[0] == pre_coord[0] and pre_coord[1]+1 == coord[1] ): # 当前后两个坐标仅纵坐标相差1时 的
                # print(coord[0] , pre_coord[0])
                x_len = x_len + 1
                pre_coord = coord
                # print("fff",x_len)
            else:       # 否则循环终止
                print("xxx", cur_coord, x_len)
                x_len = 1
                cur_coord = coord # 起始坐标位置
                pre_coord = coord  # 上一个坐标点位置

        print(coord)
        

# # print(colors)
# print(pixel)
