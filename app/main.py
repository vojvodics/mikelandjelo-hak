import requests
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import ssl

import threading

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

# Use a service account
cred = credentials.Certificate('./serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()
keywords = ['raspored', 'rezultat', ' rok', 'rok ']

TOPIC_COLLECTION = u'topics'
USER_COLLECTION = u'users'


# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage


def send_mail(email, topics):
    # Create a text/plain message
    msg = EmailMessage()
    msg.set_content('Stigla je nova vest' + str(topics))
    context = ssl.create_default_context()

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = 'Stigla je nova vest'
    msg['From'] = 'novitest123321@gmail.com'
    msg['To'] = email

    print('Sending email to ' + email)
    # Send the message via our own SMTP server.
    try:
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login("novitest123321@gmail.com", "kZf2V633wTZw")
        server.send_message(msg)
    except Exception as e:
        # Print any error messages to stdout
        print(e)
        print('there was an error')
    finally:
        server.quit() 

def main():
    print('Checking for updates...')
    topics = db.collection(TOPIC_COLLECTION)
    urls = []
    topic_dict = {}
    for topic in topics.get():
        url = topic.to_dict()['url']
        urls.append(url)
        topic_dict[url] = topic.to_dict()
        topic_dict[url]['id'] = topic.id
        # print(u'{} => {}'.format(topic.id, topic.to_dict()))
    for url in urls:
        topic = topic_dict[url]
        selector = topic['selector']
        result = requests.get(url)
        soup = BeautifulSoup(result.content, features="html.parser")
        titles = soup.find_all(selector['element'], class_=selector['class'])
        news = map(lambda x: str(x.text), titles)
        # all_a = soup.find_all('a')
        # news = filter(filter_news, all_a)
        topic.setdefault('news', [])
        old_news = topic['news']
        old_news_str = map(lambda x: x['title'], old_news)
        set_difference = set(news) - set(old_news_str)
        difference = list(map(lambda x: {'title': str(x), 'date': str(datetime.now())}, list(set_difference)))
        # print(difference)
        # print(set_difference)
        # print(old_news_str)
        # print(news)
        if len(difference) > 0:
            doc_ref = db.collection(TOPIC_COLLECTION).document(topic['id'])
            doc_ref.update({'news': topic['news'] + difference})
            # push news to notifications
            users_ref = db.collection(USER_COLLECTION)
            for usr in users_ref.get():
                user = usr.to_dict()
                send_mail(user['name'], difference)



if __name__ == "__main__":
    set_interval(main, 3)