'''
Logotouch v2 Client
===================

(used for testing pika/rabbitmq)

'''

import pika
import uuid
import json

class RpcException(Exception):
    pass

class _RpcMethodWrapper(object):
    def __init__(self, name, cb):
        self.name = name
        self.cb = cb

    def __call__(self, *args, **kwargs):
        return self.cb(self.name, *args, **kwargs)

class RpcClient(object):
    def __init__(self):
        super(RpcClient, self).__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
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
            self.connection.process_data_events()
        is_error, result = json.loads(self.response)
        if is_error:
            raise RpcException(result)
        return result

    def __getattr__(self, attr):
        return _RpcMethodWrapper(attr, self.call)

if __name__ == '__main__':
    # interactive console for testing
    from IPython import embed

    rpc = RpcClient()
    #embed()
    print rpc.fib(35)
