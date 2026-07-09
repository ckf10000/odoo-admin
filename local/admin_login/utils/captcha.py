import os
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

p = os.path.dirname(os.path.abspath(__file__))  # 获取当前py文件所在目录


def rndColor():
    """
    生成随机颜色
    :return:
    """
    return random.randint(0, 100), random.randint(10, 255), random.randint(64, 255)


def generate_captcha(width=120, height=30, char_length=4):
    bg_color = random.randint(150, 250)
    img = Image.new(mode='RGB', size=(width, height), color=(bg_color, bg_color, bg_color))
    draw = ImageDraw.Draw(img, mode='RGB')
    code = random.choices('abcdefghkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=char_length)
    font = ImageFont.truetype(os.path.join(p, "arial.ttf"), 30)  # Win
    # font = ImageFont.truetype('LiberationSans-Regular.ttf', 30)  #Linux

    draw.text((15, 0), " ".join(code), fill=(0, 0, 254), font=font)
    # for i in range(char_length):
    #     fill = (random.randint(200, 255), random.randint(0, 50), random.randint(0, 50))
    #     draw.text((i * 24+5, 0), code[i], fill=(0, 0, 254), font=font)

    # 写干扰点
    for i in range(30):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())

    # # 写干扰圆圈
    for i in range(30):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rndColor())

    # 画干扰线
    for i in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=rndColor())

    f = f'{p}\\a.png'
    img.save(f, "png")

    out = BytesIO()
    img.save(out, "png")
    return out.getvalue(), "".join(code).lower()


if __name__ == '__main__':
    generate_captcha()
