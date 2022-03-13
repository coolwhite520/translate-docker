import os
import json
import dl_translate as dlt
import time
from flask import Flask,request,jsonify
import nltk
import re
import hashlib
import hmac
import base64
import time
from zhconv import convert


app = Flask(__name__)

nltk.data.path.append("./nltk_data")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
mt = dlt.TranslationModel(BASE_DIR + "/cached_model_m2m100", model_family="m2m100", device='auto')

key_sign = "Today I want to eat noodle."

lang_code_map = dlt.utils.get_lang_code_map('m2m100')

def cut_sent(para):
    para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)
    para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)
    para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
    para = para.rstrip()
    return para.split("\n")

def GenerateHmacSign(str_old):
    digest_maker = hmac.new(key_sign.encode('utf-8'), b'', digestmod='sha1')
    digest_maker.update(str_old.encode('utf-8'))
    digest = digest_maker.digest()
    return base64.b64encode(digest).decode('utf-8')

def find_code(lang):
    for key in lang_code_map:
        if key == lang:
            return lang_code_map[key]
    return "en"

# 切分句子
@app.route('/tokenize', methods=['POST'])
def tokenize():
    ret = {}
    if request.method == 'POST':
        try:
            a = request.get_data()
            data = json.loads(a)
            content = data['content']
            src_lang = data['src_lang']
            arr_list = []
            content = content.split('\n\n')
            if src_lang == "Chinese":
                for item in content:
                    arr_list.append(cut_sent(item))
            else:
                for item in content:
                    arr_list.append(nltk.tokenize.sent_tokenize(item))
            ret["list"] = arr_list
            ret["code"] = 200
            ret["msg"] = "success"
            return jsonify(ret)
        except Exception as e:
            ret["list"] = []
            ret["len"] = 0
            ret["code"] = -1002
            ret["msg"] = e
            return jsonify(ret)
    else:
        ret["list"] = []
        ret["len"] = 0
        ret["code"] = -1003
        ret["msg"] = "error"
        return jsonify(ret)

# 翻译接口
@app.route('/translate', methods=['POST'])
def translate():
    ret = {}
    if request.method == 'POST':
        try:
            a = request.get_data()
            data = json.loads(a)
            source = data['src_lang']
            target = data['des_lang']
            content = data['content']
            timestamp = data['timestamp']
            sign = data['sign']
            str_format = "src_lang={0}&des_lang={1}&content={2}&timestamp={3}".format(source, target, content, timestamp)
            signMe = GenerateHmacSign(str_format)
            if signMe != sign:
                ret["code"] = -1001
                ret["msg"] = "验证签名错误"
                return jsonify(ret)

            now = time.time() #返回float数据
            now = int(now)
            if now - timestamp >= 60 * 2:
                ret["code"] = -1011
                ret["msg"] = "验证时间戳，已经大于了2分钟"
                return jsonify(ret)

            if source == "Chinese":
                content = cut_sent(content)
            else:
                content = nltk.tokenize.sent_tokenize(content)
            src_code = find_code(source)
            des_code = find_code(target)
            str_arr = mt.translate(content, source=src_code, target=des_code)
            trans_content = "".join(str_arr)
            if target == "zh":
                # 发现繁体就转换为简体
                trans_content = convert(trans_content, 'zh-cn')
            ret["code"] = 200
            ret["msg"] = "success"
            ret["data"] = trans_content
            return jsonify(ret)
        except Exception as e:
            ret["code"] = -1002
            ret["msg"] = e
            return jsonify(ret)
    else:
        ret["code"] = -1003
        return jsonify(ret)

@app.route('/hello')
def hello():
    time.sleep(1)
    return "hello"



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, threaded=True)
#     s = GenerateHmacSign("我爱你中国")
#     print(s)