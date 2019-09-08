# tripitaka_ocr_api

大藏经OCR接口，基于Tornado的Web服务，内部调用本机的 OCR socket 服务。

## 安装

- Python 3.6+
- `pip install -r requirements.txt`
- 运行 `python tripitaka_ocr_web.py` 或 `sh start_api.sh`

## 单页识别

'''
curl http://127.0.0.1:8010/ocr -X POST -F "file=@/foo/bar/an_image_file"
curl http://127.0.0.1:8010/ocr -X POST -F v_num=4 -F h_num=2 -F "file=@/home/sm/JS_100_1042.gif"
python tripitaka_ocr.py --v_num=4 --h_num=2 --image_file=an_image_file
'''
其中，v_num 是切分竖直参考线的个数，h_num 是切分水平参考线的个数。
上面的前两个命令是上传本地图片文件(可以是SM服务器上的)，第三个是识别已存放在OCR服务器上的文件。

## 批量识别

'''
python tripitaka_ocr.py --v_num=4 --h_num=2 --image_path=local_image_path
curl http://127.0.0.1:8010/ocr -X POST -F image_path="/foo/bar/image_image_path"
'''
