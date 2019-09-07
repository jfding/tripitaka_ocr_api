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
from tripitaka_ocr import recognize, cache
from os import path, remove
import logging

define('port', default=8010, help='run port', type=int)
define('output_path', default='/home/smjs/output', help='output path', type=str)


class MainHandler(RequestHandler):
    def post(self):
        def print_error(text):
            data['error'] = text

        img = self.request.files.get('file')
        data = dict(self.request.arguments)
        for k, v in data.items():
            data[k] = to_basestring(v[0])

        if data.get('image_path'):
            logging.info(data['image_path'])
            count = recognize(image_path=data['image_path'], reset=data.get('reset'),
                              v_num=data.get('v_num'), h_num=data.get('h_num'))
            return self.write(str(count))

        data['image_file'] = image_file = img[0]['filename'] if img else data.get('image_file')
        if not image_file:
            return self.write('need image_file')
        logging.info(str(data))

        if img:
            image_file = path.join(options.output_path, path.basename(image_file))
            with open(image_file, 'wb') as f:
                f.write(img[0]['body'])

        cache['print_error'] = print_error
        r = recognize(image_file=image_file, v_num=data.get('v_num'), h_num=data.get('h_num'), reset='clean')
        self.write(r if r else data.get('error', 'fail'))
        if img:
            remove(image_file)


def make_app():
    return Application([
        (r'/', MainHandler),
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

    # Test: curl http://127.0.0.1:8010 -X POST -F "file=@/foo/bar/JS_122_1196.gif"
