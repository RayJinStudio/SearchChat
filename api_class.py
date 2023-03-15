import openai
import requests
import urllib.parse
import re

import os
import yaml

with open(os.path.expanduser("./config.yaml"), "r") as config:
    cfg = yaml.safe_load(config)

openai.api_key = cfg["config"]["openai_api_key"]
openai.api_base = cfg["config"]["openai_api_base"]
WOLFRAMALPHA_API_ID = cfg["config"]["WOLFRAMALPHA_API_ID"]
GOOGLE_API_KEY = ""
GOOGLE_CLIENT_ID = ""
BING_API_KEY = cfg["config"]["BING_API_KEY"]

class MetaAPI():
    def __init__(self, api_name, base_url):
        self.api_name = api_name
        self.base_url = base_url

class WikiSearchAPI(MetaAPI):
    def __init__(self):
        api_name = 'Wiki Search'
        base_url = 'http://wikipedia.rayjin.top/w/api.php'
        super(WikiSearchAPI, self).__init__(api_name, base_url)
        
        
    @staticmethod
    def call(query, num_results=2):
        
        def remove_html_tags(text):
            clean = re.compile('<.*?>')
            return re.sub(clean, '', text)
        
        base_url = 'http://wikipedia.rayjin.top/w/api.php?'
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
        }
        call_url = base_url + urllib.parse.urlencode(params)
        r = requests.get(call_url)
        
        data = r.json()['query']['search']
        data = [d['title'] + ": " + remove_html_tags(d["snippet"]) for d in data][:num_results]
        # print()
        return data
        

class GoogleSearchAPI(MetaAPI):
    def __init__(self):
        api_name = 'Google Search'
        base_url = 'https://customsearch.googleapis.com/customsearch/v1?'
        super(GoogleSearchAPI, self).__init__(api_name, base_url)

    @staticmethod
    def call(query, num_results=2):
        base_url = 'https://customsearch.googleapis.com/customsearch/v1?'

        params = {
            'q': query,
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CLIENT_ID,
            'c2coff': '0',
            'num': num_results
        }

        call_url = base_url + urllib.parse.urlencode(params)
        r = requests.get(call_url)
        if "items" in r.json():
            items = r.json()["items"]
            filter_data = [
                item["title"] + ": " + item["snippet"] for item in items
            ]
            # print(filter_data)
            return filter_data
        else:
            return []
        
class BingSearchAPI(MetaAPI):
    def __init__(self):
        api_name = 'Bing Search'
        base_url = 'https://api.bing.microsoft.com/v7.0/search'
        super(GoogleSearchAPI, self).__init__(api_name, base_url)

    @staticmethod
    def call(query, num_results=3):
        base_url = 'https://api.bing.microsoft.com/v7.0/search'

        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
        params = {
                "q": query,
                "textDecorations": False,
                "textFormat": "HTML",
                "answerCount": num_results,
                "mkt": "zh-CN"
                }
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        
        #if "items" in search_results["webPages"]["value"]:
        items =  search_results["webPages"]["value"]
        filter_data = [
            dict(source=item["url"],title=item["name"],content=item["snippet"]) for item in items
        ]
            # print(filter_data)
        return filter_data
    # else:
    #     return []

class GPT3API(MetaAPI):
    def __init__(self):
        api_name = 'GPT3'
        self.model_name = {
            'tiny': 'text-ada-001',
            'small': 'text-babbage-001',
            'middle': 'text-curie-001',
            'large': "text-davinci-003",
        }
        super(GPT3API, self).__init__(api_name, '')

    @staticmethod
    def call(query, search_result, model_type='gpt-3.5-turbo'):
        prefix = "Web search results:"
        num_words = 100
        suffix = f"instructions: Using the provided web search " \
                 f"results, write a comprehensive and summarized reply to the given query in {num_words} words and in " \
                 f"English.The reply should let ChatGpt understand easily and fastly."
        if search_result == []:
            return ''
        prompt = prefix + str(search_result) + suffix + "Query:" + query
        # print(query)
        # print(prompt)
        res = openai.Completion.create(
                model=model_type,
                prompt=prompt,
                temperature=0.5,
                n=1
        )

        text = res.get('choices')[0].get("text").strip()
        # all_texts = [c.get("text").strip() for c in res.get('choices')]
        # print(all_texts)
        # json_res = json.dumps(res, ensure_ascii=False)
        # print(json_res)
        return text
    
class GPT3_5API(MetaAPI):
    def __init__(self):
        api_name = 'GPT3.5'
        super(GPT3_5API, self).__init__(api_name, '')

    @staticmethod
    def call(message, model_type='gpt-3.5-turbo'):
        if message == []:
            return ''
        res = openai.ChatCompletion.create(
                model = model_type,
                messages = message,
                n = 1
        )
        text = res['choices'][0]['message']['content']
        return text
    
    @staticmethod
    def streamCall(message, model_type='gpt-3.5-turbo'):
        if message == []:
            return ''
        res = openai.ChatCompletion.create(
                model = model_type,
                messages = message,
                stream = True
        )
        return res


class WolframAPI(MetaAPI):
    def __init__(self):
        api_name = 'wolfram'
        base_url = 'https://api.wolframalpha.com/v2/query'
        super(WolframAPI, self).__init__(api_name, base_url)
    
    @staticmethod
    def call(query, num_results=3):
        base_url = 'https://api.wolframalpha.com/v2/query'
        
        query = query.replace('+', ' plus ')
        
        params = {
            'input': query,
            'format': 'plaintext',
            'output': 'JSON',
            'appid': WOLFRAMALPHA_API_ID,
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        responseFromWolfram = requests.get(
            base_url, params=params, headers=headers)
        pods = responseFromWolfram.json()['queryresult']['pods'][:num_results]
        pods_id = [pod["id"]for pod in pods]
        subplots = [(pod['subpods']) for pod in pods]
        pods_plaintext = []
        for subplot in subplots:
            text = '\n'.join([c['plaintext'] for c in subplot])
            pods_plaintext.append(text)
        # pods_plaintext = ['\n'.join(pod['subpods']['plaintext']) for pod in pods]
        res = [pods_id[i] + ": " + pods_plaintext[i]  for i in range(len(pods_plaintext)) if pods_plaintext[i].strip() != '']
        return res
