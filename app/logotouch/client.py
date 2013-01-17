'''
Logotouch v2 Client
===================

(used for testing pika/rabbitmq)

'''

import pika
import uuid
import json
import traceback
from collections import deque
from threading import Thread, Condition

class RpcException(Exception):
    pass

class _RpcMethodWrapper(object):
    def __init__(self, name, cb):
        self.name = name
        self.cb = cb

    def __call__(self, *args):
        return self.cb(self.name, *args)

class RpcClient(object):
    def __init__(self, host='127.0.0.1', on_session_broadcast=None):
        super(RpcClient, self).__init__()
        self.on_session_broadcast = on_session_broadcast
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=host))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def bind_session(self, sessid):
        self.channel.queue_bind(exchange='session_ex',
                queue=self.callback_queue,
                routing_key='sess.{}'.format(sessid))

    def unbind_session(self, sessid):
        self.channel.queue_unbind(exchange='session_ex',
                queue=self.callback_queue,
                routing_key='sess.{}'.format(sessid))

    def on_response(self, ch, method, props, body):
        #print 'on_response()', ch, method, props
        if method.exchange == 'session_ex':
            body = json.loads(body)
            self.on_session_broadcast(method.routing_key.replace('sess.', ''), body)
            return
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, method, *args):
        body = json.dumps((method, args))
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='', routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue, correlation_id=self.corr_id),
            body=body)
        while self.response is None:
            self.idle()
        is_error, result = json.loads(self.response)
        if is_error:
            raise RpcException(result)
        return result

    def idle(self):
        self.connection.process_data_events()

    def __getattr__(self, attr):
        return _RpcMethodWrapper(attr, self.call)


class _ThreadedRpcMethodWrapper(object):
    def __init__(self, name, cb):
        self.name = name
        self.cb = cb

    def __call__(self, *args, **kwargs):
        return self.cb(self.name, *args, **kwargs)

class ThreadedRpcClient(Thread):
    def __init__(self, host='127.0.0.1', on_session_broadcast=None):
        super(ThreadedRpcClient, self).__init__()
        self.daemon = True
        self.quit = False
        self.on_session_broadcast = on_session_broadcast
        self.host = host
        self.q = deque()
        self.c = Condition()
        self.start()

    def run(self, *args, **kwargs):
        rpc = RpcClient(host=self.host,
                on_session_broadcast=self.on_session_broadcast)
        c= self.c
        q = self.q

        while not self.quit:
            with c:
                try:
                    method, args, callback = q.pop()
                except IndexError:
                    c.wait(0.25)
                    if not q:
                        rpc.idle()
                    continue

            try:
                result = getattr(rpc, method)(*args)
            except Exception, e:
                traceback.print_exc()
                callback(None, error=e)
                continue

            try:
                if callback:
                    callback(result, error=None)
            except:
                traceback.print_exc()


    def __getattr__(self, attr):
        return _ThreadedRpcMethodWrapper(attr, self.schedule)

    def schedule(self, method, *args, **kwargs):
        with self.c:
            self.q.appendleft((method, args, kwargs.get('callback')))
            self.c.notify()




if __name__ == '__main__':
    # interactive console for testing
    from IPython import embed

    rpc = RpcClient()
    embed()
    print rpc.fib(35)
