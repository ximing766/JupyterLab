import gradio as gr
import requests

def call_api(text):
    response = requests.get(f"http://localhost:8000/process?data={text}")
    return response.json()["result"]

# 自动生成网页界面
gr.Interface(fn=call_api, inputs="text", outputs="text").launch()