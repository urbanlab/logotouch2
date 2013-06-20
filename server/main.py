'''
Logotouch v2 Server
===================

'''

import pika
import redis
import json
import logging
from time import time
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('server')
rpcmethods = {}

def rpcmethod(f):
    rpcmethods[f.__name__] = f
    return f

def cname(i, key):
    return 'corpus.' + str(i) + '.' + key

class rdefaultdict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(rdefaultdict, self).__init__(*args, **kwargs)
        self.default_factory = rdefaultdict

class LogotouchServer(object):

    def __init__(self):
        super(LogotouchServer, self).__init__()
        self.start_redis()
        self.start_pika()

    def start_redis(self):
        self.redis = r = redis.StrictRedis()

        # very first time we created the server, initiate
        # note: further database change can be handled from the lt.version
        if not r.exists('lt.version'):
            r.set('lt.version', 1)
            r.set('lt.session', 0)
            r.set('lt.corpus', 0)
            r.set('lt.users', 0)

    def start_pika(self):
        logger.info('Connecting to RabbitMQ')
        #self.credentials = pika.PlainCredentials('user', 'pass')
        # + , credentials=... in the Parameters
        self.parameters = pika.ConnectionParameters('localhost')
        self.conn = pika.SelectConnection(
                self.parameters, self.on_connected)

    def run(self):
        conn = self.conn
        try:
            conn.ioloop.start()
        except KeyboardInterrupt:
            conn.close()
            conn.ioloop.start()

    def on_connected(self, conn):
        logger.info('Create channel')
        conn.channel(self.on_channel_open)

    def on_channel_open(self, chan):
        self.chan = chan
        logger.info('Declare rpc_queue')
        self.chan.queue_declare(queue='rpc_queue',
                callback=self.on_queue_declared)
        self.chan.exchange_declare(exchange='session_ex',
                type='direct',
                callback=self.on_session_queue_declared)

    def on_queue_declared(self, frame):
        logger.info('Rpc queue ready')
        self._rpc_ready = True
        self._start_consume()

    def on_session_queue_declared(self, frame):
        logger.info('Session queue ready')
        self._session_ready = True
        self._start_consume()

    def _start_consume(self):
        if not hasattr(self, '_rpc_ready') or \
                not hasattr(self, '_session_ready'):
            return
        logger.info('Start consuming')
        self.chan.basic_qos(prefetch_count=1)
        self.chan.basic_consume(self.handle_delivery)#, queue='rpc_queue')

    def handle_delivery(self, ch, method, header, body):
        logger.info('[x] %r', (ch, method, header, body))

        # xxx remove it for prod ?
        if method.redelivered:
            ch.basic_publish(exchange='',
                routing_key=header.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=header.correlation_id),
                body=json.dumps(('error', 'redelivery')))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # unpack the func name, and the args
        func, args = json.loads(body)

        # call the method
        try:
            rfunc = rpcmethods.get(func)
            if not rfunc:
                raise Exception('Unknow method %r' % func)
            result = rfunc(self, *args)
            result = json.dumps((False, result))
        except Exception, e:
            logger.warn(e)
            import traceback
            traceback.print_exc()
            result = json.dumps((True, repr(e)))

        # publish the response
        ch.basic_publish(exchange='',
            routing_key=header.reply_to,
            properties=pika.BasicProperties(
                correlation_id=header.correlation_id),
            body=result)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    @rpcmethod
    def get_rpc_methods(self):
        return rpcmethods.keys()

    #
    # Logotouch RPC methods
    #

    @rpcmethod
    def get_available_corpus(self):
        r = self.redis
        res = {}
        keys = r.keys('corpus.*.name')
        for key in keys:
            # strip '.name'
            cid = key[7:-5]
            res[cid] = self.get_corpus_info(cid)
        return res

    def get_corpus_info(self, cid):
        r = self.redis
        get = r.get
        return {
            'id': cid,
            'title': get(cname(cid, 'name')),
            'lastupdate': get(cname(cid, 'lastupdate')),
            'version': get(cname(cid, 'version')),
            'count': get(cname(cid, 'count')),
            'author': get(cname(cid, 'author')),
            'email': get(cname(cid, 'email')),
            'is_public': get(cname(cid, 'is_public')),
            'is_editable': get(cname(cid, 'is_editable'))}

    @rpcmethod
    def new_corpus(self, title, author, email):
        r = self.redis
        cid = r.incr('lt.corpus')
        key = 'corpus.{}'.format(cid)
        r.set('{}.name'.format(key), title)
        r.set('{}.lastupdate'.format(key), time())
        r.set('{}.version'.format(key), 0)
        r.set('{}.count'.format(key), 0)
        r.set('{}.author'.format(key), author)
        r.set('{}.email'.format(key), email)
        r.set('{}.is_public'.format(key), 0)
        r.set('{}.is_editable'.format(key), 0)
        return cid

    @rpcmethod
    def get_corpus(self, cid):
        r = self.redis
        get = r.get
        res = rdefaultdict()

        if not get(cname(cid, 'name')):
            return None

        res['info'] = {
            'id': cid,
            'title': get(cname(cid, 'name')),
            'lastupdate': get(cname(cid, 'lastupdate')),
            'version': get(cname(cid, 'version')),
            'count': int(get(cname(cid, 'count'))),
            'author': get(cname(cid, 'author')),
            'email': get(cname(cid, 'email'))}

        keys = r.keys('corpus.{0}.*'.format(cid))
        words = res['words']
        for key in keys:
            part = key.split('.')[2:]
            l = len(part)
            if l == 2:
                words[part[0]][part[1]] = get(key)
            elif l == 3:
                words[part[0]][part[1]][part[2]] = get(key)

        return res

    @rpcmethod
    def new_session(self, email, corpus, password=None):
        r = self.redis
        sessid = r.incr('lt.session')
        key = 'sess.{}'.format(sessid)
        r.set('{}.corpus'.format(key), corpus)
        r.set('{}.lastaccess'.format(key), time())
        r.set('{}.email'.format(key), email)
        r.set('{}.pw'.format(key), password)
        self.user_push_session(email, sessid)
        return sessid

    @rpcmethod
    def join_session(self, email, sessid):
        r = self.redis
        corpus_id = r.get('sess.{}.corpus'.format(sessid))
        if not corpus_id:
            return
        r.set('sess.{}.lastaccess'.format(sessid), time())
        sentences_count = r.llen('sess.{}.sentences'.format(sessid))
        self.broadcast_to_session(sessid, ('cmd.join', ))
        self.user_push_session(email, sessid)
        return { 'sessid': sessid, 'corpusid': corpus_id,
                 'sentences_count': sentences_count }

    @rpcmethod
    def add_sentence(self, sessid, sentence):
        r = self.redis
        sentence = json.dumps(sentence)
        key = 'sess.{}.sentences'.format(sessid)
        r.lpush(key, sentence)
        self.broadcast_to_session(sessid, ('cmd.newsentence', r.llen(key), sentence))
        return True

    @rpcmethod
    def get_sentences(self, sessid):
        r = self.redis
        key ='sess.{}.sentences'.format(sessid)
        count = r.llen(key)
        return r.lrange(key, 0, count)

    @rpcmethod
    def get_last_sessions(self, email):
        return [self.get_session_infos(sess) for sess in
                self.user_get_sessions(email)]

    def get_session_infos(self, sessid):
        r = self.redis
        key = 'sess.{}'.format(sessid)
        cid = r.get('{}.corpus'.format(key))
        return {
            'sessid': sessid,
            'corpusid': r.get('{}.corpus'.format(sessid)),
            'lastaccess': r.get('{}.lastaccess'.format(sessid)),
            'sentences_count': r.llen('{}.sentences'.format(sessid)),
            'corpus': self.get_corpus_info(cid)}

    def user_get_sessions(self, email):
        r = self.redis
        uid = self.get_user_id(email)
        key = 'user.{}.last_sessions'.format(uid)
        count = r.llen(key)
        return r.lrange(key, 0, count)

    def user_push_session(self, email, sessid):
        uid = self.get_user_id(email)
        key = 'user.{}.last_sessions'.format(uid)
        self.redis.lpush(key, sessid)

    def get_user_id(self, email):
        r = self.redis
        keys = r.keys('user.*.email')
        for key in keys:
            if r.get(key) == email:
                return key.split('.')[1]
        return self.new_user(email)

    def new_user(self, email):
        r = self.redis
        uid = r.incr('lt.users')
        key = 'user.{}'.format(uid)
        r.set('{}.email'.format(key), email)
        return uid

    def broadcast_to_session(self, sessid, data):
        logger.info('[b] %r', (sessid, data))
        self.chan.basic_publish(exchange='session_ex',
                routing_key='sess.{}'.format(sessid),
                body=json.dumps(data))

if __name__ == '__main__':
    LogotouchServer().run()
