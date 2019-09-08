#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 调用OCR本地服务识别页面图像
@time: 2019/9/4
"""

from os import path, system, makedirs
from glob2 import glob
from datetime import datetime
from PIL import Image
import socket
import re
import sys
import json
import time

__version__ = '0.0.3 190908'
ROOT = '/srv/deeptext.v3'
INPUT_IMAGE_PATH = '/srv/deeptext.v3/Web_v2/cache/images/'
OUT_TXT_PATH = '/srv/deeptext.v3/Web_v2/cache/recognition_label/'
cache = dict(count=0, web_mode=False)


def print_error(text):
    if cache.get('print_error'):
        cache['print_error'](text.strip())
    sys.stderr.write(text)


def call_server(name, req, ip, port, timeout=120):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    start_time = datetime.now()
    result = None
    try:
        s.connect((ip, port))
        time.sleep(0.1)
    except ConnectionError:
        print_error('Connection %s:%d refused\n' % (ip, port))
        return 0, None
    try:
        s.settimeout(timeout)
        req_s = req if isinstance(req, str) else json.dumps(req)
        s.send(req_s.encode())
        result = s.recv(4096).decode()
        if result.startswith('{'):
            result = json.loads(result)
        else:
            print_error('%s: %s\n' % (name, result))
            result = None
    except (OSError, ValueError) as e:
        print_error('[%s:%d] %s: %s\n' % (ip, port, name, str(e).split(']')[-1]))
    finally:
        s.close()

    return round((datetime.now() - start_time).microseconds / 1000), result


def recognize(image_path='', image_file='', output_path='/home/smjs/output', v_num=1, h_num=1,
              reset=False, ip='127.0.0.1'):
    """
    OCR主函数
    :param image_path: 图片根路径
    :param image_file: 特定的图片文件，指定后将忽略image_path参数
    :param output_path: 识别结果的输出目录，每个页面输出一个JSON文件
    :param v_num: vertical layouts
    :param h_num: horizontal layouts
    :param reset: 是否重新识别
    :return: 
    """

    def page_recognize(img_file):
        name = path.basename(path.splitext(img_file)[0])
        out_file = path.join(output_path, name + '.json')
        if not reset and path.exists(out_file):
            return

        if cache['web_mode']:
            img_file = img_file.replace(ROOT, '')
        im = Image.open(img_file)
        if not im:
            print_error('%s not exist\n' % img_file)
            return
        img_size = im.size
        jpg_file = path.join(INPUT_IMAGE_PATH, '%s.jpg' % name)

        if not img_file.lower().endswith('.jpg'):
            img_l = im.convert('L')
            img_l.save(jpg_file)
        else:
            system('rm -f {0}; ln -fs {1} {0}'.format(jpg_file, img_file))
        img_file = jpg_file

        txt_files = [path.join(OUT_TXT_PATH, '%s_task%d.txt' % (name, i)) for i in range(1, 4)]
        system('rm -f %s;' % ' '.join(txt_files))

        req1 = dict(img_file=img_file.replace(ROOT, ''), saved_txt_file=txt_files[0].replace(ROOT, ''))
        req2 = dict(img_file=img_file.replace(ROOT, ''), input_txt=txt_files[0].replace(ROOT, ''),
                    output_txt=txt_files[1].replace(ROOT, ''))
        req.update(dict(img_file=img_file.replace(ROOT, ''), input_txt=txt_files[0].replace(ROOT, ''),
                        output_txt=txt_files[2].replace(ROOT, '')))
        ms1, char_detect = call_server(name, req1, ip, 8009)  # 单字检测
        ms2, char_rec = call_server(name, req2, ip, 8008) if char_detect else (0, 0)  # 单字识别
        ms3, line_rec = call_server(name, req, ip, 8007) if char_rec else (0, 0)  # 列切分识别

        pos, text = [], []  # 每个字框的坐标和文字
        texts = []  # 每列的文字
        r = dict(imgname=name, imgsize=dict(width=img_size[0], height=img_size[1]),
                 run_ms=ms1 + ms2 + ms3, v_num=v_num, h_num=h_num)
        if line_rec:
            for line in open(txt_files[1]).readlines():  # 83 723 142 778 解
                pos.append([int(item) for item in line.split(' ')[:4]])
                text.append(line.strip().split(' ')[-1])
            cc = [float(t.split(' ')[0]) for t in open(txt_files[0]).readlines()]
            assert len(cc) == len(pos) == len(text)

            if path.exists(txt_files[2]):
                texts = [t.strip() for t in open(txt_files[2]).readlines()]

            r.update(dict(chars_cc=cc, chars_pos=pos, chars_text=text, lines_text=texts,
                          lines_pos=line_rec.get('Line_coors'), num_pos=line_rec.get('Num_coor')))
            with open(out_file, 'w') as f:
                json.dump(r, f, ensure_ascii=False)
            cache['count'] += 1

        print('%s: %d chars, %d lines, %d %d %d ms' % (name, len(pos), len(texts), ms1, ms2, ms3))
        if img_file.startswith('/Web_v2/'):
            system('rm -f %s;' % img_file)
        if reset == 'clean':
            system('rm -f %s;' % out_file)
        system('rm -f %s;' % ' '.join(txt_files))

        return r

    v_num, h_num = int(v_num or 1), int(h_num or 1)
    assert v_num > 0 and h_num > 0
    req = dict(multiple_layouts=v_num > 1 or h_num > 1, v_num=v_num, h_num=h_num)
    reset = reset in [1, True, '1', 'true']

    if not path.exists(output_path):
        try:
            makedirs(output_path)
        except OSError:
            print_error('fail to create %s\n' % output_path)
            output_path = '.'
    if image_file:
        return page_recognize(image_file)
    elif image_path:
        if cache['web_mode']:
            image_path = image_path.replace(ROOT, '')
        assert path.exists(image_path)
        match = re.compile(r'\.(jpg|gif|png|tiff|tif)$')
        files = glob(path.join(image_path, '*', '*.*')) + glob(path.join(image_path, '*.*'))
        files = sorted([f for f in files if match.search(f)])
        count = 0
        for image_file in files:
            if page_recognize(image_file):
                count += 1
        print('%d pages processed' % count)
        return count
    else:
        print('Usage: python tripitaka_ocr.py --image_file=<filename> --output_path=<path> --v_num=? --h_num=?')


if __name__ == '__main__':
    import fire

    fire.Fire(recognize)
