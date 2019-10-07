"""

	PrintProgress by Arnaud de Broissia

"""

import sys
import time
import os
import json
import datetime
# import pynvml


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[1;36m'
    OKGREEN = '\033[1;32m'
    WARNING = '\033[93m'
    FAIL = '\033[1;31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class void_printer:
    def __init__(self, message=None, printInterval=1):
        pass

    def __call__(self, message):
        return self

    def __enter__(self, timer=False):
        return self

    def __exit__(self, type, value, traceback):
        if all((type, value, traceback)):
            raise type, value, traceback


class printProg:
    """
        Context for clean printing of state of the system.
    """

    def __init__(self, message, printInterval=1, monitorGPU=False):
        self.progress_info_dir = os.path.split(__file__)[0]+"/logs/"
        self.monitorGPU = monitorGPU
        if self.monitorGPU:
            import pynvml
            pynvml.nvmlInit()
        self.message = [message]
        self.printInterval = printInterval
        self.lastPrint = 0
        self.status = [""]
        self.level_count = -1
        self.on_line = False
        self.timers=[-1]
        self.PID = os.getpid()
        self.host = os.uname()[1]
        self.start_time=time.time()
        self.progress_info_file= self.progress_info_dir + str(self.PID) +"_" + self.message[0].replace(" ", "_").replace("/", "_")+".json"
        self.infos = {}

        self.writeProgress()


    def __call__(self, message, timer=False):
        self.message.append(message)
        self.status.append("")
        if timer:
            self.timers.append(1)
        else:
            self.timers.append(-1)
        return self

    def __enter__(self):
        self.level_count += 1
        self.status[-1] = bcolors.OKBLUE + "..." + bcolors.ENDC
        if self.timers[-1] == 1:
            self.timers[-1] = time.time()
        if self.on_line:
            sys.stdout.write("\n")
            self.on_line = False
        if self.monitorGPU:
            import pynvml
            nb_gpu = pynvml.nvmlDeviceGetCount()
            used_gpus = []
            for i in range(nb_gpu):
                gpu = pynvml.nvmlDeviceGetHandleByIndex(0)
                processes = pynvml.nvmlDeviceGetComputeRunningProcesses(gpu)
                for pr in processes:
                    if pr.pid == self.PID:
                        used_gpus.append("GPU_"+str(i))
                        break
                if len(used_gpus) != 0:
                    self.addInfo(GPU=used_gpus)
        self.printStatus()
        return self

    def __exit__(self, type, value, traceback):
        if all((type, value, traceback)):
            if type == KeyboardInterrupt:
                self.status[-1] = bcolors.WARNING + "INTERRUPTED" + bcolors.ENDC
            else:
                self.status[-1] = bcolors.FAIL + "FAILED" + bcolors.ENDC
                self.printError(str(type))
            self.printStatus(True)
            self.level_count -= 1
            del self.status[-1]
            del self.message[-1]
            if type != KeyboardInterrupt:
                raise type, value, traceback
        else:
            self.status[-1] = bcolors.OKGREEN + "OK" + bcolors.ENDC
            if self.timers[-1] != -1:
                self.status[-1] +=bcolors.OKGREEN + " in " +  "{0:.2f}".format(time.time() - self.timers[-1]) + "s"+ bcolors.ENDC
            self.printStatus(True)
            self.level_count -= 1
            del self.status[-1]
            del self.timers[-1]
            del self.message[-1]

    def printInferior(self, f1, f2):
        if f1 < f2 and self.lastPrint % self.printInterval == 0:
            if f2 != 0:
                self.status[-1] = bcolors.OKBLUE + str(float(f1) / float(f2) * 100.0)[:4] + bcolors.ENDC
            else:
                self.status[-1] = bcolors.OKBLUE + "Err" + bcolors.ENDC
            self.printStatus()
        return f1 < f2

    def printWarning(self, message):
        if self.on_line:
            sys.stdout.write("\n")
            self.on_line = False
        self.indent_message()
        sys.stdout.write("[" + bcolors.WARNING + "Warning" + bcolors.ENDC + "] " + message + "\033[K\n")
        sys.stdout.flush()
        self.printStatus()

    def printError(self, message):
        if self.on_line:
            sys.stdout.write("\n")
            self.on_line = False
        self.indent_message()
        sys.stdout.write("[" + bcolors.FAIL + "ERROR" + bcolors.ENDC + "] " + message + "\033[K\n")
        sys.stdout.flush()
        self.printStatus()

    def printResult(self, flag, message):
        if self.on_line:
            sys.stdout.write("\n")
            self.on_line = False
        self.indent_message()
        sys.stdout.write("[" + bcolors.OKBLUE + flag + bcolors.ENDC + "] " + message + "\033[K\n")
        sys.stdout.flush()
        self.printStatus()

    def printStatus(self, retour=False):
        self.indent_message()
        sys.stdout.write(self.message[-1] + " [")
        sys.stdout.write(self.status[-1] + "]\033[K")
        if retour:
            sys.stdout.write("\n")
            self.on_line = False
        else:
            sys.stdout.write("\r")
            self.on_line = True
        sys.stdout.flush()
        self.writeProgress()

    def setStatus(self, status, printInterval=False):
        self.status[-1] = bcolors.OKBLUE + status + bcolors.ENDC
        if not printInterval or self.lastPrint % self.printInterval == 0:
            self.printStatus()
        if printInterval:
            self.lastPrint += 1

    def indent_message(self):
        for i in range(self.level_count):
            sys.stdout.write("-")

    def loop(self, loop_def, refresh_intervals=10):
        if type(loop_def) == int:
            loop_def = range(loop_def)
        if type(loop_def) is list:
            nb_elements = len(loop_def)
        else:
            nb_elements = -1
        self.addInfo( loop_progress = 0, size_loop = nb_elements)
        loop_start_time = time.time()
        for i, loop_el in enumerate(loop_def):
            if i%refresh_intervals==0:
                if nb_elements==-1:
                    self.setStatus(str(loop_el))
                    self.addInfo(loop_progress=i, )
                else:
                    self.setStatus(str(float("%.2f" % (float(i) / nb_elements * 100.0)))+"%")
                    remaining_time = (time.time()-loop_start_time) / max(i, 1) * (nb_elements-i)
                    self.addInfo(loop_progress=i, loop_remaining_time = str(datetime.timedelta(seconds=remaining_time)))
            yield loop_el
        self.addInfo(loop_progress="Done")

    def writeProgress(self):
        with open(self.progress_info_file + "_tmp", "w") as f:
            json.dump({"PID" : self.PID,
                       "HOST" : self.host,
                       "START_TIME" : self.start_time,
                       "messages": self.message,
                       "STATUS": self.status,
                       "infos" : self.infos}, f, indent=4)
        os.rename(self.progress_info_file + "_tmp", self.progress_info_file)

    def addInfo(self, **kwargs):
        for k in list(kwargs.keys()):
            self.infos[k]=kwargs[k]