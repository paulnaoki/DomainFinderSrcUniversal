from multiprocessing import Process, Queue, Event
import multiprocessing
from threading import RLock, Thread
import time
from DomainFinderSrc.Utilities.MachineInfo import MachineInfo
from collections import Iterable
from DomainFinderSrc.Utilities.Logging import PrintLogger


class ContinFucFeedback:
    def __init__(self, finished, state, callback_data, need_to_restart=False):
        """
        The data structure used to pass feedback to the controller: MemoryControlPs
        :param finished: indicate if a program has finished
        :param state: program latest state while running, which in turn will plug back into program in the next cycle if
         the work is unfinished
        :param callback_data: the callback data that will be pass beyond next control level
        :return:
        """
        self.finished = finished
        self.need_to_restart = need_to_restart
        self.callback_data = callback_data
        self.state = state

    def __str__(self):
        return "finish: " + str(self.finished) + " " + str(self.callback_data) + " " + str(self.state)


class FeedbackInterface:
    """
    Interface define how to pass data back to the controller: MemoryControlPs
    Subclass need to implement this interface in order to communicate with the controller
    """
    _feedback_queue_key = 'feedback_queue'
    _last_state_key = 'last_state'
    _sampling_f_key = 'sampling_f'
    _queue_lock_key = "queue_lock"

    def __init__(self, **kwargs):
        self._feedback_queue = kwargs.get(FeedbackInterface._feedback_queue_key, None)
        self._last_state = kwargs.get(FeedbackInterface._last_state_key, None)
        self._sampling_f = kwargs.get(FeedbackInterface._sampling_f_key, 1)
        self._queue_lock = kwargs.get(FeedbackInterface._queue_lock_key, None)
        self._last_feedback = None
        self._state_lock = RLock()
        self._stop_send_event = Event()
        self._is_last_post_important = False
        self._sending_wait = 1/self._sampling_f  # send back every second

    @staticmethod
    def get_feedback_parameter(queue, state, frequency: float, queue_lock: multiprocessing.RLock)->dict:
        return {FeedbackInterface._feedback_queue_key: queue,
                FeedbackInterface._last_state_key: state,
                FeedbackInterface._sampling_f_key: frequency,
                FeedbackInterface._queue_lock_key: queue_lock}

    def _populate_with_state(self):
        """
        invoke this method at the end of your __init__ to override internal state of you method or object
        :return:
        """
        self.populate_with_state(self._last_state)

    def populate_with_state(self, state):
        """
        FeedbackInterface, subclass implement this method to
        :param state: the state from previous
        :return:
        """
        raise NotImplementedError

    def get_state(self):
        """
        FeedbackInterface, subclass this so that the controller can gather state info, which in turn will feedback into next iteration
        :return:
        """
        raise NotImplementedError

    def get_callback_data(self):
        """
        FeedbackInterface, subclass this so that any callback data can be gathered by the controller
        :return:
        """
        raise NotImplementedError

    def is_programme_finshed(self):
        """
        FeedbackInterface, indicate if the programme has finished execution, if not it goes to next iteration
        :return:
        """
        raise NotImplementedError

    def is_progamme_need_restart(self):
        """
        FeedbackInterface, indicate if the programme needs to be restarted, if not it goes to next iteration
        """
        return False

    def _sending(self):
        with self._state_lock:
            is_finished = self.is_programme_finshed()
            need_retart = self.is_progamme_need_restart()
            self._last_feedback = ContinFucFeedback(is_finished,
                                                    self.get_state(), self.get_callback_data(),
                                                    need_to_restart=need_retart)
            #print("sending back", self._last_feedback.__dict__)
            if self._feedback_queue is not None and not self._is_last_post_important:
                with self._queue_lock:
                    self._feedback_queue.put(self._last_feedback)
                    if is_finished or need_retart: # only send once important msg, otherwise it will retart or kill twice the current process
                        self._is_last_post_important = True

    def _send_back_feedback(self):
        if self._feedback_queue is not None and hasattr(self._feedback_queue, 'put'):
            while not self._stop_send_event.is_set():
                self._sending()
                time.sleep(self._sending_wait)
        else:
            print("something wrong in feedback queue")

    def _start_sending_feedback(self):
        """
        This has to be invoked in the beginning of long running program to send back feedback in a thread
        :return:
        """
        #print("start sending feedback")
        t = Thread(target=self._send_back_feedback)
        t.start()

    def _end_sending_feedback(self):
        """
        call this at the end of your long running method
        :return:
        """
        #print("sending end event")
        self._sending()  # send the last event, which contains finished flag
        self._stop_send_event.set()


class MemoryCheckerThread(Thread):
    def __init__(self, pid: int, sampling_f: float, mem_limit: int, stop_event: Event, callback):
        super(MemoryCheckerThread, self).__init__()
        #print("init memory thread")
        self._pid = pid
        self._mem_limit = mem_limit
        self._exceed_limit = False
        self._sampling_f = sampling_f
        self._wait = 1/sampling_f
        self._stop_event = stop_event
        self._callback = callback

    def run(self):
        #print("running memory monitor")
        while True:
            if self._stop_event.is_set():
                #print("external stop")
                break
            else:
                mem = MachineInfo.get_memory_process(self._pid)
                #print("process use: ", mem, " MB")
                if mem > self._mem_limit:
                    self._exceed_limit = True
                    self._callback(True)
                time.sleep(self._wait)


class MemoryControlPs:
    _sampling_f = 2
    MEM_CONTROL_EVENT_KEY = "memory_control_terminate_event"  # function with this event will be able to terminate not only via feedback

    def __init__(self, func, func_args: Iterable=None, func_kwargs: dict=None,
                 callback=None,  mem_limit=200, external_stop_event: Event=None):
        self._func = func
        self.callback = callback
        self._mem_limit = mem_limit
        self._res_lock = multiprocessing.RLock()
        if func_args is None:
            self._args = ()
        else:
            self._args = func_args
        if func_kwargs is None:
            self._kwargs = {}
        else:
            self._kwargs = func_kwargs
        self._exceed_lock = RLock()
        self._exceed_limit = False
        self._feedback_queue = Queue()
        self._last_state = None
        self._inner_process = Process()
        self._output_update_t = Thread()
        self._mem_monitor_t = Thread()
        self._stop_event = Event()
        self._finished_lock = RLock()
        self.finished = False
        self._external_stop_event = external_stop_event
        self._feedback_terminate_event = Event()
        self._kwargs.update({MemoryControlPs.MEM_CONTROL_EVENT_KEY: self._feedback_terminate_event})

    def get_last_state(self):
        return self._last_state

    def memory_limit_callback(self, boolean):
        with self._exceed_lock:
            self._exceed_limit = boolean

    def queue_feedback(self, data):
        if isinstance(data, ContinFucFeedback) and not self._stop_event.is_set():
            if not self.finished:
                if data.finished:
                    with self._finished_lock:  # terminate process
                        self.finished = True
                elif data.need_to_restart:   # restart process
                    with self._exceed_lock:
                        self._exceed_limit = True
                else:
                    self._last_state = data.state
                if self.callback is not None:
                    self.callback(data.callback_data)

    def is_exceed_memory_limit(self):
        """
        Get by external event, to know if a process has exceed its memory limit
        :return:
        """
        with self._exceed_lock:
            exceed = self._exceed_limit
        return exceed

    @staticmethod
    def update_feedback(sampling_f: float, output_queue: Queue, stop_event: Event, callback):
        wait_t = 1/sampling_f
        #print("start update feedback")
        while True:
            if stop_event.is_set():
                break
            try:
                while not output_queue.empty():
                    obj = output_queue.get(block=False, timeout=wait_t)
                    if obj is not None:
                        callback(obj)
            finally:
                #print("go to sleep")
                time.sleep(wait_t)
        #print("start end feedback")

    def empty_feedback_queue(self):
        try:
            PrintLogger.print("in MemoryControlPs: trying to empty queue")
            while not self._feedback_queue.empty():
                obj = self._feedback_queue.get(block=False, timeout=0.001)
                if obj is not None:
                    self.memory_limit_callback(obj)
        except Exception as ex:
            PrintLogger.print("in MemoryControlPs.empty_feedback_queue()" + str(ex))

    def kill(self):  # kill the process
        if self._inner_process.is_alive():
            with self._res_lock:
                self._inner_process.terminate()

        self._stop_event.set()  # _output_update_t and _mem_monitor_t are listening to the stop event

        if self._output_update_t.is_alive():
            self._output_update_t.join()
        if self._mem_monitor_t.is_alive():
            self._mem_monitor_t.join()

    def _re_start(self):
        self.kill()
        self._res_lock = multiprocessing.RLock()
        self._stop_event.clear()
        self._exceed_limit = False
        self._kwargs.update(FeedbackInterface.get_feedback_parameter(self._feedback_queue, self._last_state,
                                                                     MemoryControlPs._sampling_f/2, self._res_lock))  # twice slower
        self._inner_process = Process(target=self._func, args=self._args,
                                      kwargs=self._kwargs)
        self._inner_process.start()
        pid = self._inner_process.pid
        #print("inner_process started: pid: ", pid)
        self._output_update_t = Thread(target=MemoryControlPs.update_feedback,
                                       args=(MemoryControlPs._sampling_f, self._feedback_queue, self._stop_event,
                                             self.queue_feedback))  # normal speed, so it satisfy Shannon sampling freq.
        self._mem_monitor_t = MemoryCheckerThread(pid=pid, sampling_f=MemoryControlPs._sampling_f,
                                                  mem_limit=self._mem_limit,
                                                  stop_event=self._stop_event, callback=self.memory_limit_callback)
        self._output_update_t.start()
        self._mem_monitor_t.start()

    def start(self):
        #print("monitor process started: pid: ", os.getpid())
        wait_t = 2/MemoryControlPs._sampling_f
        self._re_start()
        while True:
            with self._finished_lock:
                finished = self.finished
            if (self._external_stop_event is not None and self._external_stop_event.is_set()) or finished \
                    or self._feedback_terminate_event.is_set():
                #print("external set stop or process finished, stop now")
                time.sleep(2)  # wait for data passing through the queue at max 2 s
                self.empty_feedback_queue()
                self.kill()
                break
            with self._exceed_lock:
                if self._exceed_limit:
                   #print("exceed limit, restart it")
                    self._re_start()
            time.sleep(wait_t)
        #print("monitor process stopped")



