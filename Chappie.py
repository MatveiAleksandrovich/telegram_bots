import os
import time

import telegram
import logging
import requests
from dotenv import load_dotenv

load_dotenv()


try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as err:
    logging.error(f'Возникла проблема с переменными. {err}')


PRAKTIKUM_API_URL = 'https://praktikum.yandex.ru/api/user_api/{}'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name == '':
        logging.warning('Имя домашней работы не передано.')
    statuses = {
        'rejected': 'rejected',
        'approved': 'approved',
        'reviewing': 'reviewing',
    }
    verdicts = {
        'ok': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
        'try again': 'К сожалению в работе нашлись ошибки.'
    }
    if status not in statuses:
        logging.info('Передан неизвестный статус.')
        return f'Передан неизвестный статус: {status}'
    verdict = verdicts['ok']
    if status == statuses['rejected']:
        verdict = verdicts['try again']
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    empty_dict = []
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(
            url=PRAKTIKUM_API_URL.format('homework_statuses/'),
            headers=headers,
            params=params,
        )
        return homework_statuses.json()
    except requests.ConnectionError as err:
        logging.exception(
            f'Exception occurred. Ошибка: {err} '
        )
        return empty_dict


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except telegram.error:
        logging.warning('Ошибка отправки сообщения.')
    logging.info('Сообщение отправлено в telegram.')


def main() -> dict:
    SLEEP_TIME_5_SEC = time.sleep(5)
    SLEEP_TIME_5_MIN = time.sleep(300)
    try:
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    except telegram.error:
        logging.warning('Ошибка: бот запускаться не хочет.')
    logging.debug('Запуск telegram бота.')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                homework = new_homework.get('homeworks')
                parse_status = homework[0]
                send_message(parse_status, bot_client)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            SLEEP_TIME_5_MIN

        except Exception as e:
            logging.error(f'Бот столкнулся с ошибкой: {e}')
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
            SLEEP_TIME_5_SEC


if __name__ == '__main__':
    main()
