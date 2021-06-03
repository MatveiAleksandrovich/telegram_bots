import os
import datetime
import telegram
import logging
import nltk
import requests
import uuid
import json
from newsapi import NewsApiClient
from newspaper import Article
from dotenv import load_dotenv
from time import sleep
from requests import Request, Session
from math import ceil
from textblob import TextBlob


load_dotenv()
nltk.download('punkt')

try:
    CURRENCY_TOKEN = os.environ['CURRENCY_TOKEN']
    NEWS_TOKEN = os.environ['NEWSAPI_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID_1 = os.environ['TELEGRAM_CHAT_ID_MY']
    CHAT_ID_2 = os.environ['TELEGRAM_CHAT_ID_YARMAK']
    NEWS_API = NewsApiClient(api_key=NEWS_TOKEN)
    ENDPOINT = os.environ['endpoint']
    TRANSLATE_KEY = os.environ['subscription_key']
    LOCATION = os.environ['location']
except KeyError as error:
    logging.error(f'Возникла проблема с переменными. {error}')


CURRENCY_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
URLS = []
SUBSCRIBER_ID = [CHAT_ID_2, CHAT_ID_1]
NEWS = []


def translate(text):
    subscription_key = os.environ['subscription_key']
    endpoint = os.environ['endpoint']
    location = os.environ['location']

    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': ['ru']
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': '206763d7e1b44ac6873ffb5661bcda2b',
        'Ocp-Apim-Subscription-Region': 'global',
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{
        'text': text
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()

    r = json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))
    p = json.loads(r)
    return p[0]['translations'][0]['text']


def get_headline_news():
    news_line = NEWS_API.get_top_headlines(sources='bbc-news')
    return news_line


def get_urls():
    urls = []
    for i in get_headline_news()['articles']:
        urls.append(i['url'])
    return urls


def summarize_news():
    for url in get_urls()[0:3]:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        blob = TextBlob(article.text)
        sentiment_score = blob.sentiment.polarity
        sentiment = '🌓'

        if sentiment_score <= -0.3:
            sentiment = '🌑'
        elif sentiment_score >= 0.3:
            sentiment = '🌕'

        NEWS.append(
            f'{sentiment} *Title*:\n{article.title}.\n\n'
            f'*Summary*:\n{article.summary}\n\n'
            f'*Read more*:\n{article.url}'
        )
        # NEWS.append(
        #     f'{sentiment} *Новость*:\n{translate(str(article.title))}.\n\n'
        #     f'{sentiment} *Title*:\n{article.title}.\n\n'
        #     f'*В общем*:\n{translate(article.summary)}\n\n'
        #     f'*Summary*:\n{article.summary}\n\n'
        #     f'*Читать подробнее*:\n{article.url}'
        # )
    return NEWS


def clear_data():
    NEWS.clear()


bot_client = telegram.Bot(token=TELEGRAM_TOKEN)


def send_message_news(message, bot_client):
    for i in range(len(message)):
        bot_client.send_message(chat_id=CHAT_ID_1, text=message[-1], parse_mode='Markdown', disable_web_page_preview=True)
        bot_client.send_message(chat_id=CHAT_ID_2, text=message[-1])
        message.pop()
    return


def send_message_resume(bot_client):
    time_now = datetime.datetime.now()
    hour_minute = time_now.strftime('%H:%M')
    message = f'That is all for {hour_minute}.\nBe yourself and you got it! ❤💯'
    bot_client.send_message(chat_id=CHAT_ID_1, text=message, parse_mode='Markdown')
    return


def send_at_time():
    hours = ['5', '15', '23']
    while True:
        time_now = datetime.datetime.now()
        if str(time_now.hour) in hours:
            answer = summarize_news()
            send_message_currency(bot_client)
            send_message_news(answer, bot_client)
            send_message_resume(bot_client)
        sleep(3600)


parameters_doge = {
    'slug': 'dogecoin',
    'convert': 'USD',
}
parameters_btc = {
    'slug': 'bitcoin',
    'convert': 'USD',
}
parameters_ethereum = {
    'slug': 'ethereum',
    'convert': 'USD',
}

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': CURRENCY_TOKEN,
}

session = Session()
session.headers.update(headers)


def send_message_currency(bot_client):
    response_doge = session.get(CURRENCY_URL, params=parameters_doge)
    response_btc = session.get(CURRENCY_URL, params=parameters_btc)
    response_ethereum = session.get(CURRENCY_URL, params=parameters_ethereum)

    doge_price = (json.loads(response_doge.text)['data']['74']['quote']['USD']['price'])
    doge_24h_percent_change = (json.loads(response_doge.text)['data']['74']['quote']['USD']['percent_change_1h'])

    btc_price = (json.loads(response_btc.text)['data']['1']['quote']['USD']['price'])
    btc_24h_percent_change = (json.loads(response_btc.text)['data']['1']['quote']['USD']['percent_change_1h'])

    ethereum_price = (json.loads(response_ethereum.text)['data']['1027']['quote']['USD']['price'])
    ethereum_24h_percent_change = (
        json.loads(response_ethereum.text)['data']['1027']['quote']['USD']['percent_change_1h']
    )
    if doge_24h_percent_change >= 0:
        progress_doge = '📈'
    else:
        progress_doge = '📉'

    if ethereum_24h_percent_change >= 0:
        progress_eth = '📈'
    else:
        progress_eth = '📉'

    if btc_24h_percent_change >= 0:
        progress_btc = '📈'
    else:
        progress_btc = '📉'

    message = (f'*DOGECOIN*: {ceil(doge_price * 100) / 100.0}$ ({ceil(doge_24h_percent_change * 100) / 100.0}% / hour) {progress_doge}\n\n'
               f'*BITCOIN*: {ceil(btc_price * 100) / 100.0}$ ({ceil(btc_24h_percent_change * 100) / 100.0}% / hour) {progress_btc}\n\n'
               f'*ETHEREUM*: {ceil(ethereum_price * 100) / 100.0}$ ({ceil(ethereum_24h_percent_change * 100) / 100.0}% / hour) {progress_eth}\n\n'
               f'_Have a nice day! Everything will be OK!\n'
               f'Below there are the summ of top news around the world, be up to date!_')
    bot_client.send_message(chat_id=CHAT_ID_1, text=message, parse_mode='Markdown')
    return


send_at_time()