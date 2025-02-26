# -*- coding: utf-8 -*-
#    sss
# author: oldj
# blog: http://oldj.net
# email: oldj.wu@gmail.com
#

u"""
pyHeatMap
@link https://github.com/oldj/pyheatmap

"""

import os
import random
from PIL import Image
from PIL import ImageDraw2
from .inc import cf

import sys

if sys.version > '3':
    PY3 = True
else:
    PY3 = False


class HeatMap(object):
    def __init__(self,
                 data,
                 base=None,
                 width=0,
                 height=0
                 ):
        u""""""

        assert type(data) in (list, tuple)
        assert base is None or os.path.isfile(base)
        assert cf.is_num(width) and cf.is_num(height)
        assert width >= 0 and height >= 0

        count = 0
        data2 = []
        for hit in data:
            if len(hit) == 3:
                x, y, n = hit
            elif len(hit) == 2:
                x, y, n = hit[0], hit[1], 1
            else:
                raise Exception(u"length of hit is invalid!")

            data2.append((x, y, n))
            count += n

        self.data = data2
        self.count = count
        self.base = base
        self.width = width
        self.height = height
        self.save_as = None

        if not self.base and (self.width == 0 or self.height == 0):
            w, h = cf.get_max_size(data)
            self.width = self.width or w
            self.height = self.height or h

    def __mk_img(self, base=None):
        u"""生成临时图片"""

        base = base or self.base
        self.__im0 = None

        if base:
            str_type = (str,) if PY3 else (str, unicode)
            self.__im0 = Image.open(base) if type(base) in str_type else base
            self.width, self.height = self.__im0.size

        self.__im = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

    def __paint_hit(self, x, y, color):
        u"""绘制点击小叉图片"""

        im = self.__im
        width, height = self.width, self.height
        im.putpixel((x, y), color)

        for i in (1, 2):
            pos = (
                (x + i, y + i),
                (x + i, y - i),
                (x - i, y + i),
                (x - i, y - i),
            )
            for ix, iy in pos:
                if 0 <= ix < width and 0 <= iy < height:
                    im.putpixel((ix, iy), color)

    def clickmap(self, save_as=None, base=None, color=(255, 0, 0, 255), data=None):
        u"""绘制点击图片"""

        self.__mk_img(base)

        data = data or self.data
        for hit in data:
            x, y, n = hit
            if n == 0 or x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue

            self.__paint_hit(x, y, color)

        self.__add_base()
        if save_as:
            self.save_as = save_as
            self.__save()

        return self.__im

    def __heat(self, heat_data, x, y, n, template):
        u""""""

        l = len(heat_data)
        width = self.width
        p = width * y + x

        for ip, iv in template:
            p2 = p + ip
            if 0 <= p2 < l:
                heat_data[p2] += iv * n

    def __paint_heat(self, heat_data, colors):
        u""""""

        import re

        im = self.__im
        rr = re.compile(", (\d+)%\)")
        dr = ImageDraw2.ImageDraw.Draw(im)
        width = self.width
        height = self.height

        max_v = max(heat_data)
        if max_v <= 0:
            # 空图片
            return

        r = 240.0 / max_v
        heat_data2 = [int(i * r) - 1 for i in heat_data]

        size = width * height
        _range = range if PY3 else xrange
        for p in _range(size):
            v = heat_data2[p]
            if v > 0:
                x, y = p % width, p // width
                color = colors[v]
                alpha = int(rr.findall(color)[0])
                if alpha > 50:
                    al = 255 - 255 * (alpha - 50) // 50
                    im.putpixel((x, y), (0, 0, 255, al))
                else:
                    dr.point((x, y), fill=color)

    def __add_base(self):
        if not self.__im0:
            return

        self.__im0.paste(self.__im, mask=self.__im)
        self.__im = self.__im0

    def sample(self, max_count=None, rate=None):

        count = self.count
        if count == 0:
            return self.data

        if rate and 0 < rate < 1:
            count = int(self.count * rate)
        if max_count and count > max_count:
            count = max_count

        if count == 0 or count >= self.count:
            return self.data

        data = []
        _range = range if PY3 else xrange
        for x, y, n in self.data:
            for i in _range(n):
                data.append((x, y))

        sample = random.sample(data, count)
        data = {}
        for x, y in sample:
            key = (x, y)
            data[key] = data.get(key, 0) + 1

        data2 = []
        for key in data:
            x, y = key
            data2.append((x, y, data[key]))

        return data2

    def heatmap(self, save_as=None, base=None, data=None, r=10):
        u"""绘制热图"""

        self.__mk_img(base)

        circle = cf.mk_circle(r, self.width)
        heat_data = [0] * self.width * self.height

        data = data or self.data

        for hit in data:
            x, y, n = hit
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue

            self.__heat(heat_data, x, y, n, circle)

        self.__paint_heat(heat_data, cf.mk_colors())
        self.__add_base()

        if save_as:
            self.save_as = save_as
            self.__save()

        return self.__im

    def __save(self):

        save_as = os.path.join(os.getcwd(), self.save_as)
        folder, fn = os.path.split(save_as)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        self.__im.save(save_as)
        self.__im = None


def test():
    u"""测试方法"""

    print("load data..")
    data = []
    f = open("../examples/test_data.txt")
    for ln in f:
        a = ln.split(",")
        if len(a) != 2:
            continue
        x, y = int(a[0]), int(a[1])
        data.append([x, y])
    f.close()

    print("painting..")
    # 开始绘制
    hm = HeatMap(data)
    hm.clickmap(save_as="hit.png")
    hm.heatmap(save_as="heat.png")

    print("done.")


if __name__ == "__main__":
    test()
