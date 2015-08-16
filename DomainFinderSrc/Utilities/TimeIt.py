import time
from functools import wraps
from DomainFinderSrc.Utilities.Logging import PrintLogger, ErrorLogger
__author__ = 'Pauli Zhang'


def timeit(ref: str="timeit", log_if_longer: float=0):
    """
    time the execution time of a function, usage:

    @timeit()
    def my_long_running_func(*args, **kwargs):
        some code...
        pass

    :param ref: the ref name stored in error log if it takes too long to run
    :param log_if_longer: the time limit in seconds
    :return: a decorator can be used by any function
    """
    def timed(method):

        @wraps(method)
        def wrap(*args, **kw):
            ts = time.time()
            result = method(*args, **kw)
            te = time.time()
            gap = te-ts
            if gap > log_if_longer > 0:
                PrintLogger.print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, gap))
                ErrorLogger.log_error(ref, ValueError("Operation took too long."), "completed in " + str(gap))
            elif log_if_longer == 0:
                # PrintLogger.print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, gap))
                PrintLogger.print('%r took %2.2f sec' % (method.__name__, gap))

            return result
        return wrap

    return timed