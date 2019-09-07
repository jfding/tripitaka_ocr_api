# tripitaka_ocr_api

大藏经OCR接口，基于Tornado的Web服务，内部调用本机的 OCR socket 服务。

## 安装

- Python 3.6+
- `pip install -r requirements.txt`
- 运行 `python tripitaka_ocr_web.py` 或 `sh start_api.sh`

## 测试

- `curl http://127.0.0.1:8010 -X POST -F "file=@/foo/bar/an_image_file"`
- `curl http://127.0.0.1:8010 -X POST -F image_path="/foo/bar/image_image_path"`

## 批量识别

`python tripitaka_ocr.py --image_path=local_image_path`
