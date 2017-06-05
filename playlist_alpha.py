import collections
import logging

import lib.api as API

import os

import urllib2
from urllib2 import urlopen, URLError, HTTPError

from copy import copy

from flask import Flask, json
from flask_ask import Ask, question, statement, audio, current_stream, logger

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.INFO)

## Define myweb/ proxy parameters

myweb = 'https://80fa83b6.ngrok.io/'
#proxy_port = 'http://125.88.74.122:84'
proxy_port = 'http://111.13.7.42:81'
#proxy_port = 'http://211.140.139.222:8081'

##Create netease Object
userID = 'NETEASEACCOUNT'
passwd = 'PASSWORD'

#Login Netease account and Daily Signin
#netease = API.NetEase()
#netease.login(userID, passwd)
#netease.daily_signin(1)
#netease.daily_signin(0)


SongList = []

def dlfile(url):
    # Open the url
    try:
	proxy = urllib2.ProxyHandler({'http': proxy_port})
	opener = urllib2.build_opener(proxy)
        f = opener.open(url)
        print "downloading " + url
        # Open our local file for writing
        with open(os.path.basename(url), "wb") as local_file:
            local_file.write(f.read())
    #handle errors
    except HTTPError, e:
        print "HTTP Error:", e.code, url
    except URLError, e:
        print "URL Error:", e.reason, url


class QueueManager(object):
    """Manages queue data in a seperate context from current_stream.

    The flask-ask Local current_stream refers only to the current data from Alexa requests and Skill Responses.
    Alexa Skills Kit does not provide enqueued or stream-histroy data and does not provide a session attribute
    when delivering AudioPlayer Requests.

    This class is used to maintain accurate control of multiple streams,
    so that the user may send Intents to move throughout a queue.
    """

    def __init__(self, urls):
        self._urls = urls
        self._queued = collections.deque(urls)
        self._history = collections.deque()
        self._current = None

    @property
    def status(self):
        status = {
            'Current Position': self.current_position,
            'Current URL': self.current,
            'Next URL': self.up_next,
            'Previous': self.previous,
            'History': list(self.history)
        }
        return status

    @property
    def up_next(self):
        """Returns the url at the front of the queue"""
        qcopy = copy(self._queued)
        current_url = qcopy.popleft()
        currentMP3 = current_url.split('/')[-1]

        try:
            if os.path.exists('./'+currentMP3):
                return myweb+currentMP3
            else:
                dlfile(current_url)
                return myweb+currentMP3

        except IndexError:
            return None

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, url):
        self._save_to_history()
        self._current = url

    @property
    def history(self):
        return self._history

    @property
    def previous(self):
        history = copy(self.history)
        try:
            return history.pop()
        except IndexError:
            return None

    def add(self, url):
        self._urls.append(url)
        self._queued.append(url)

    def extend(self, urls):
        self._urls.extend(urls)
        self._queued.extend(urls)

    def _save_to_history(self):
        if self._current:
            self._history.append(self._current)

    def end_current(self):
        self._save_to_history()
        self._current = None

    def step(self):
        self.end_current()
        self._current = self._queued.popleft()
        currentMP3 = self._current.split('/')[-1]

        if os.path.exists('./'+currentMP3):
            self._current = myweb+currentMP3
            return self._current
        else:
            dlfile(self._current)
            self._current = myweb+currentMP3
            return self._current

    def step_back(self):
        self._queued.appendleft(self._current)
        self._current = self._history.pop()
        return self._current

    def reset(self):
        self._queued = collections.deque(self._urls)
        self._history = []

    def start(self):
        self.__init__(self._urls)
        return self.step()

    @property
    def current_position(self):
        return len(self._history) + 1


queue = QueueManager([])
@ask.launch
def launch():
    card_title = 'NetEase Music'
    text = 'Welcome to NetEase Music. Ask me to start the recommendation playlist.'
    prompt = 'You can ask start playlist.'
    netease = API.NetEase()
    netease.login(userID, passwd)
    netease.daily_signin(1)
    netease.daily_signin(0)
    rmdlist = netease.recommend_playlist()
    for i in range(0,len(rmdlist)-1):
#        if rmdlist[i]:
            SongList.append(rmdlist[i]['mp3Url'])
            print SongList[i]
    global queue
    queue = QueueManager(SongList)
    return question(text).reprompt(prompt).simple_card(card_title, text)


@ask.intent('PlaylistDemoIntent')
def start_playlist():
    speech = 'Heres your daily recommended play list.'
    stream_url = queue.start()
    return audio(speech).play(stream_url)


# QueueManager object is not stepped forward here.
# This allows for Next Intents and on_playback_finished requests to trigger the step
@ask.on_playback_nearly_finished()
def nearly_finished():
    global queue
    if queue.up_next:
        _infodump('Alexa is now ready for a Next or Previous Intent')
        # dump_stream_info()
        next_stream = queue.up_next
        _infodump('Enqueueing {}'.format(next_stream))
        return audio().enqueue(next_stream)
    else:
        _infodump('Nearly finished with last song in playlist')


@ask.on_playback_finished()
def play_back_finished():
    global queue
    _infodump('Finished Audio stream for track {}'.format(queue.current_position))
    if queue.up_next:
        queue.step()
        _infodump('stepped queue forward')
        dump_stream_info()
    else:
        return statement('You have reached the end of the playlist!')


# NextIntent steps queue forward and clears enqueued streams that were already sent to Alexa
# next_stream will match queue.up_next and enqueue Alexa with the correct subsequent stream.
@ask.intent('AMAZON.NextIntent')
def next_song():

    if queue.up_next:
        speech = 'playing next song'
        next_stream = queue.step()
        _infodump('Stepped queue forward to {}'.format(next_stream))
        dump_stream_info()
        return audio(speech).play(next_stream)
    else:
        return audio('There are no more songs in the queue')


@ask.intent('AMAZON.PreviousIntent')
def previous_song():
    if queue.previous:
        speech = 'playing previously song'
        prev_stream = queue.step_back()
        dump_stream_info()
        return audio(speech).play(prev_stream)

    else:
        return audio('There are no songs in your playlist history.')


@ask.intent('AMAZON.StartOverIntent')
def restart_track():
    if queue.current:
        speech = 'Restarting current track'
        dump_stream_info()
        return audio(speech).play(queue.current, offset=0)
    else:
        return statement('There is no current song')


@ask.on_playback_started()
def started(offset, token, url):
    _infodump('Started audio stream for track {}'.format(queue.current_position))
    dump_stream_info()


@ask.on_playback_stopped()
def stopped(offset, token):
    _infodump('Stopped audio stream for track {}'.format(queue.current_position))

@ask.intent('AMAZON.PauseIntent')
def pause():
    seconds = current_stream.offsetInMilliseconds / 1000
    msg = 'Paused the Playlist on track {}, offset at {} seconds'.format(
        queue.current_position, seconds)
    _infodump(msg)
    dump_stream_info()
    return audio(msg).stop().simple_card(msg)


@ask.intent('AMAZON.ResumeIntent')
def resume():
    seconds = current_stream.offsetInMilliseconds / 1000
    msg = 'Resuming the Playlist on track {}, offset at {} seconds'.format(queue.current_position, seconds)
    _infodump(msg)
    dump_stream_info()
    return audio(msg).resume().simple_card(msg)


@ask.session_ended
def session_ended():
    return "", 200

def dump_stream_info():
    status = {
        'Current Stream Status': current_stream.__dict__,
        'Queue status': queue.status
    }
    _infodump(status)


def _infodump(obj, indent=2):
    msg = json.dumps(obj, indent=indent)
    logger.info(msg)


if __name__ == '__main__':
    app.run(debug=True)
