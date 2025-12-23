import subprocess
import requests
import json
import os
from cryptography.fernet import Fernet
import base64
import hashlib
from datetime import datetime
import sys


PUSH_URL = os.environ.get("PUSH_URL")
raw_key = os.environ.get("ENCRYPT_KEY")
if not raw_key:
    raise RuntimeError("ENCRYPT_KEY not found")

key = base64.urlsafe_b64encode(
    hashlib.sha256(raw_key.encode()).digest()
)

cipher = Fernet(key)

def send_push_notification(url, data):
    """发送推送消息"""
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("推送结果:", response.json())
    else:
        print("请求失败，状态码:", response.status_code)

# 定义处理函数
def extract_and_format_info(result):
    # 如果 result 是字符串，尝试将其解析为字典
    if isinstance(result, str):
        try:
            result = eval(result)  # 使用 eval 将字符串字典转为真正的字典
        except Exception as e:
            return f"Error: 无法解析输入的 result，错误信息：{e}"

    if 'data' in result:
        data = result['data']
        count = data.get('count', 0)
        courses = data.get('courses', [])
        output = [f"成绩数量：{count}"]
        for course in courses:
            title = course.get('title', '')
            grade = course.get('grade', '')
            output.append(f"{title}：{grade}")
        result_formated = str(datetime.now()) + "\n" + "\n".join(output)
        return result_formated
    return "Error: result 中缺少 'data' 字段"

def run_example_script():
    """运行 example.py 并获取其输出"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "zfn_api.py")
        result = subprocess.run(
            [sys.executable, script_path],  # 如果需要指定 Python 版本，可以改为 python3 等
            capture_output=True,
            text=True
        )
        if result.returncode == 0:  # 检查脚本是否正常运行
            return result.stdout.strip()
        else:
            print(f"zfn_api.py 执行失败，错误信息：{result.stderr}")
            return None
    except Exception as e:
        print(f"运行 zfn_api.py 时出错：{e}")
        return None

def main():
    try:
        with open("data.txt", "rb") as f:
            encrypted = f.read()
        f.close()
        last_result = cipher.decrypt(encrypted).decode()

    except FileNotFoundError:
        last_result = None

    print()
    print("当前时间:", datetime.now())
    print("开始运行 zfn_api.py ...")
    current_result = run_example_script()

    if current_result is not None:  # 确保运行结果有效
        if last_result is None:
            print("首次运行，结果为：")
            print(extract_and_format_info(current_result))
            payload = {
                "title": "首次查询",  # 消息标题
                "content": extract_and_format_info(current_result),  # 消息内容
            }
            send_push_notification(PUSH_URL, payload)
        elif current_result != last_result:
            print("运行结果发生变化，新的结果为：")
            print(extract_and_format_info(current_result))
            payload = {
                "title": "成绩更新",  # 消息标题
                "content": extract_and_format_info(current_result),  # 消息内容
            }
            send_push_notification(PUSH_URL, payload)
        else:
            print("运行结果相同，无变化。结果为：")
            print(extract_and_format_info(current_result))

        # 更新上一次的运行结果
        encrypted_data = cipher.encrypt(current_result.encode())
        with open("data.txt", "wb") as f:
            f.write(encrypted_data)
        f.close()


if __name__ == "__main__":
    main()
