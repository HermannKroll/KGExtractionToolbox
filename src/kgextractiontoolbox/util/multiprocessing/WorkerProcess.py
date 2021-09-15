import multiprocessing


class WorkerProcess(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
