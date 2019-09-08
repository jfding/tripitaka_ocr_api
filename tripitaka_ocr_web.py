#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: OCR本地服务的文件转发服务
@time: 2019/9/7
"""

from tornado.web import RequestHandler, Application
import tornado.ioloop
from tornado.escape import to_basestring
from tornado.options import define, options
from os import path, remove
import tripitaka_ocr as c
import logging

define('port', default=8010, help='run port', type=int)
define('output_path', default='/home/smjs/output', help='output path', type=str)
define('socket_ip', default='172.17.0.1', help='output path', type=str)

c.cache['web_mode'] = True
c.INPUT_IMAGE_PATH = c.INPUT_IMAGE_PATH.replace(c.ROOT, '')
c.OUT_TXT_PATH = c.OUT_TXT_PATH.replace(c.ROOT, '')


class MainHandler(RequestHandler):
    def get(self):
        return self.write('Tripitaka OCR API v%s, %d pages processed.' % (c.__version__, c.cache['count']))


class RecognizeHandler(RequestHandler):
    def post(self):
        def print_error(text):
            data['error'] = text

        img = self.request.files.get('file')
        data = dict(self.request.arguments)
        for k, v in data.items():
            data[k] = to_basestring(v[0])

        if data.get('image_path'):
            logging.info(data['image_path'])
            count = c.recognize(image_path=data['image_path'], reset=data.get('reset'),
                                v_num=data.get('v_num'), h_num=data.get('h_num'), ip=options.socket_ip)
            return self.write(str(count))

        data['image_file'] = image_file = img[0]['filename'] if img else data.get('image_file')
        if not image_file:
            return self.write('need image_file')
        logging.info(str(data))

        if img:
            image_file = path.join(options.output_path, path.basename(image_file))
            with open(image_file, 'wb') as f:
                f.write(img[0]['body'])

        c.cache['print_error'] = print_error
        r = c.recognize(image_file=image_file, v_num=data.get('v_num'), h_num=data.get('h_num'),
                        reset='clean', ip=options.socket_ip)
        if r and not r.get('chars_text'):
            r['error'] = data.get('error', 'fail')
        self.write(r if r else data.get('error', 'fail'))
        if img:
            remove(image_file)


def make_app():
    return Application([
        (r'/', MainHandler),
        (r'/ocr', RecognizeHandler),
    ], debug=True)


if __name__ == '__main__':
    options.parse_command_line()
    app = make_app()
    app.listen(options.port)
    logging.info('Start the service on http://127.0.0.1:%d' % options.port)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logging.info('Stop the service')

    # Test: curl http://127.0.0.1:8010/ocr -X POST -F "file=@/foo/bar/JS_122_1196.gif"
