import requests

response_main = requests.post("https://changing-egret-erinsarlak-af2a6dfd.koyeb.app")
print('Web Application Response:\n', response_main.text, '\n\n')


data = {"text":"tell me about tufts"}
response_llmproxy = requests.post("https://changing-egret-erinsarlak-af2a6dfd.koyeb.app/query", json=data)
print('LLMProxy Response:\n', response_llmproxy.text)
