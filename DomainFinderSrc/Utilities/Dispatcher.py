from threading import Thread


class ThreadWithReturn(Thread):
    def __init__(self, *args, **kwargs):
        super(ThreadWithReturn, self).__init__(*args, **kwargs)

        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        super(ThreadWithReturn, self).join(*args, **kwargs)
        return self._return


class TimeoutDispatcher:
    def __init__(self, func, timeout=None, func_kwarg: dict=None):
        """
        :param func: function to dispatch
        :param timeout: timeout in sec, None for forever
        :param func_kwarg: parameters to pass to function
        :return:
        """
        self._func = func
        self._timeout = timeout
        self._func_arg = func_kwarg

    def dispatch(self):
        t = ThreadWithReturn(target=self._func, kwargs=self._func_arg)
        t.start()
        return t.join(self._timeout)
