from multiprocessing.managers import BaseManager, Server
import queue
import time
# ref: https://docs.python.org/3.4/library/multiprocessing.html#multiprocessing-managers


class QueueManager(BaseManager):
    _DEFAULT_HOST = '127.0.0.1'
    _PORT_FOR_CRAWLER = 10001
    _PORT_FOR_CONTROL = 10000
    Method_Whois_Input = 'get_whois_input_queue'
    Method_Whois_Output = 'get_whois_output_queue'
    Method_FilterPool_Input = 'get_filter_pool_input'
    Method_FilterPool_Output = 'get_filter_pool_output'
    Methods_Crawler = [Method_Whois_Input, Method_Whois_Output]
    Methods_Control = [Method_FilterPool_Input, Method_FilterPool_Output]
    MachineSettingCrawler = (_DEFAULT_HOST, _PORT_FOR_CRAWLER, Methods_Crawler)
    MachineSettingControl = (_DEFAULT_HOST, _PORT_FOR_CONTROL, Methods_Control)
    # AddrWhoisInputQueue = (_DEFAULT_HOST, _PORT_FOR_CRAWLER, Method_Whois_Input)
    # AddrWhoisOutputQueue = (_DEFAULT_HOST, _PORT_FOR_CRAWLER, Method_Whois_Output)
    # AddrFilterPoolInputQueue = (_DEFAULT_HOST, _PORT_FOR_CONTROL, Method_FilterPool_Input)
    # AddrFilterOutputQueue = (_DEFAULT_HOST, _PORT_FOR_CONTROL, Method_FilterPool_Output)


def get_queue_client(parameters: tuple, method: str, max_retries=60) -> (QueueManager, queue.Queue):
    """
    get a queue client for a server address and its method.
    :param addr: the address the client is connecting to, for instance: ('127.0.0.1', 10000).
    :param method: a method name in str.
    :param max_retries: number of connection retries before total failure.
    :return: a queue manager and its queue, the queue is None upon connection failure.
    """
    host, port, methods = parameters
    if method not in methods:
        raise ValueError("method is not within scope.")
    for item in methods:
        QueueManager.register(item)
    m = QueueManager((host, port),)
    count = 0
    result_queue = None
    while count < max_retries:
        try:
            m.connect()
            #result_queue = m.get_whois_input_queue()
            result_queue = getattr(m, method, None)()
        except:
            pass
            #m.shutdown()

        if result_queue is not None:
            break
        else:
            print("wait for queue...")
            count += 1
            time.sleep(1)
    if result_queue is None:
        print("getting queue failed.")
    else:
        print("queue acquired.", method)
    return m, result_queue


def get_queue_server(parameters: tuple) -> Server:
    """
    get the sever which servers queues communication. maybe need some improvment. do not know how register work!!, dont accept dynamically creating callable
    :param parameters: the address of the queue server and a list of methods, for instance: ('127.0.0.1', 10000, [x, y, z]).
    :return: the server.
    """
    host, port, methods = parameters
    if port == QueueManager._PORT_FOR_CRAWLER:
        whois_input_q = queue.Queue()
        whois_output_q = queue.Queue()
        QueueManager.register(QueueManager.Method_Whois_Input, callable=lambda: whois_input_q)
        QueueManager.register(QueueManager.Method_Whois_Output, callable=lambda: whois_output_q)
    else:
        filter_pool_input_q = queue.Queue()
        filter_pool_output_q = queue.Queue()
        QueueManager.register(QueueManager.Method_FilterPool_Input, callable=lambda: filter_pool_input_q)
        QueueManager.register(QueueManager.Method_FilterPool_Output, callable=lambda: filter_pool_output_q)
    m = QueueManager((host, port),)
    return m.get_server()