import json

from api_class import GPT3API, WikiSearchAPI, WolframAPI, GPT3_5API, BingSearchAPI
import threading 

import json
import re

def search(content):
    call_list = content['calls']
    if(len(call_list) == 0):
        return ""
    # global search_data
    global call_res
    call_res = {}
    def google_search(query, num_results=4,summarzie = False):
        search_data = BingSearchAPI.call(query, num_results=num_results)
        if summarzie:
            summary_data = GPT3API.call(query, search_data)
            call_res['google/' + query] = summary_data
        else:
            call_res['google/' + query] = search_data
        
    def wiki_search(query, num_results=3,summarzie = False):
        search_data = WikiSearchAPI.call(query, num_results=num_results)
        if summarzie:
            summary_data = GPT3API.call(query, search_data)
            call_res['wiki/' + query] = summary_data
        else:
            call_res['wiki/' + query] = search_data
        call_res['wiki/' + query] = search_data
    def wolfram_search(query, num_results=3):
        search_data = WolframAPI.call(query, num_results)
        call_res['wolfram/' + query] = search_data
    all_threads = []
    google_summarize = False
    google_cnt = 0
    wiki_summarize = False
    wiki_cnt = 0
    for call in call_list[:]:
        q = call['API']
        if q.lower() == 'google':
            google_cnt += 1
        if q.lower() == 'wikisearch':
            wiki_cnt += 1
    if google_cnt > 3:
        google_summarize = True
    if wiki_cnt > 2:
        wiki_summarize = True
    for call in call_list[:]:
        q = call['query']
        api = call['API']
        print("正在", api.replace("Google","Bing"), "搜索: ", q)
        if api.lower() == 'google':
            t = threading.Thread(target=google_search, args=[q, 5, google_summarize])
        elif api.lower() == 'wikisearch':
            t = threading.Thread(target=wiki_search, args=[q, 2, wiki_summarize])
        elif api.lower() == 'calculator':
            t = threading.Thread(target=wolfram_search, args=[q])
        else:
            continue
        all_threads.append(t)
    for t in all_threads:
        t.start()
    for t in all_threads:
        t.join()
    print(json.dumps(call_res, ensure_ascii=False))
    return json.dumps(call_res, ensure_ascii=False)

def APIQuery(query):
    with open("template.txt", "r", encoding='utf-8') as f:
        prompt = f.read()
    messages = [
        {"role": "system", "content": prompt },
        {"role": "user", "content": query}
        ]
    response = GPT3_5API.call(messages)
    # print("Ray:", response)
    pattern = r"(\{[\s\S\n]*\"calls\"[\s\S\n]*\})"
    match = re.search(pattern, response)
    if match:
        json_data = match.group(1)
        return json.loads(json_data)
    return json.loads("{\"calls\":[]}")

def SumReply(query, apicalls):
    # with open("summary.txt", "r",encoding='utf-8') as f:
    #     prompt = f.read()
    messages = [
        {"role": "system", "content": "请结合以下搜索到的结果回答user的问题, 可以在参考的地方后面加上source\n" + apicalls },
        {"role": "user", "content": query}
        ]
    # prompt = prompt.replace("{query}", query)
    # prompt = prompt.replace("{apicalls}", apicalls)
    response = GPT3_5API.streamCall(messages)

    res_text = ''

    flag = 0

    for event in response:
        if flag == 0 or event['choices'][0]['finish_reason']:
            flag = 1
            continue
        event_text = event['choices'][0]['delta']['content']
        print(event_text, end="", flush=True)
        res_text += event_text

    return res_text

def DirectReply(query):
    # with open("summary.txt", "r",encoding='utf-8') as f:
    #     prompt = f.read()
    messages = [
            {"role": "user", "content": query}
        ]
    # prompt = prompt.replace("{query}", query)
    # prompt = prompt.replace("{apicalls}", apicalls)
    response = GPT3_5API.streamCall(messages)

    res_text = ''

    flag = 0

    for event in response:
        if flag == 0 or event['choices'][0]['finish_reason']:
            flag = 1
            continue
        event_text = event['choices'][0]['delta']['content']
        print(event_text, end="", flush=True)
        res_text += event_text

    return res_text


if __name__ == "__main__":
    query = input()
    query = query.strip()
    if(query == ''):
        exit()
    #APIQuery1(query)
    call_res = search(APIQuery(query))
    print('\nChatGpt: ' )
    if call_res == "":
        DirectReply(query)
    else:
        SumReply(query, call_res)