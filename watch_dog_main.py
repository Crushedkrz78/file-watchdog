"""
Experimental Script to generate a Watchdog in Python to check file changes into a specified directory,
when a file is modified, then a thread should be launched to check if file has to be processed.

There's an indicator into the file which defines if the file (Or the process related to that file has been completed)
"""
# Base OS Functionalities
import threading
import time
import sys
import os
import shutil
from datetime import datetime
# Log Functionality
import logging
from logging.handlers import TimedRotatingFileHandler
# Watchdog Functionality
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler

# Global variables
fileThreads = {}

# Define a main function to generate the Watchdog Instance
class guardog:
    def __init__(self):
        # self.guard_status = True
        """ WatchDog Initial Setup """
        # self.watch_patterns = "*"
        # self.watch_ignore_patterns = "" # Files to be ignored
        # self.watch_ignore_directories = True # True if we want to be notified just for regular files, not for directories)
        # self.watch_case_sensitive = True # True made the patterns we previously introduced case sensitive
        self.watch_go_recursively = False
        """ Logger Initial Setup """
        # self.notifications_path = "C:\\Git\\python-watchdog-multithread\\file_repo" # Set the path in CARMDATA
        # self.logger = None
        """ Email Sender Initial Setup """
        # self.crew_mail = {}
        # self.sender_address = ''
        # self.sender_pass = ''
        """ Misc Initial Setup"""
        self.file_path = None
        self.file_repo = "pbs_opt_info"
        # self.carmdata_path = ""
        
    """ def set_log(self):
        formatter = logging.Formatter("%(asctime)s - %(leveltime)s - %(message)s")
        log_file = os.path.join(self.notifications_path, "logs", "email_notifications.log")
        handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, encoding="utf-8")
        handler.suffix = "%Y-%m-%d"
        handler.setFormatter(formatter)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler) """
        
    """ def on_created(self, event):
        self.notification_file_path = event.src_path
        if event.event_type == 'created':
            self.logger.debug("New File: %s has been created!" % self.notification_file_path)
        elif event.event_type == 'modified':
            self.logger.debug("New File: %s has been modified!" % self.notification_file_path)
        
        # self.move_to_archive()
        print("Something happened with my file! D:") """
    
    """ def move_to_archive(self):
        file_name = self.notification_file_path.split("/")[-1]
        archive_path = os.path.join(self.notifications_path, "Archive", file_name)
        if not os.path.isdir(archive_path):
            self.logger.debug("Creating Archive Directory: %s" %archive_path)
            os.makedirs(archive_path)
        try:
            shutil.move(self.notification_file_path, archive_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%N_%S%f')
            self.logger.debug("%s moved to archive: %s" %(file_name, archive_path))
        except KeyboardInterrupt:
            self.logger.warning("Fatal Error") """
    
    def main(self, path):
        self.file_path = os.path.join(path, self.file_repo)
        event_handler = Handler()
        
        # Observer initialization
        dog_observer = Observer()
        dog_observer.schedule(event_handler, self.file_path, recursive=self.watch_go_recursively)
        dog_observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            dog_observer.stop()
            print("Observer Stopped")
        
        dog_observer.join()
        
class Handler(FileSystemEventHandler):
    """
    This class handles any file event ocurred inside an specified
    directory. For this functionality only new created files will be handled.
    Modified existing files would be ignored.
    An event happens when a file is created. This file
    contains a path to a matador.log file related to a SubPlan
    optimization job. When the file is created, then a thread is
    created and launched to keep track until the optimization
    job is finished.
    """
    
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        
        elif event.event_type == 'created':
            print("Created new file on path: %s" % event.src_path)
            createdFileName = event.src_path
            threadName = createdFileName.split('/')[-1]
            print("ThreadName: %s" % threadName)
            fileThreads[createdFileName] = dogThread(1, threadName, createdFileName, 2) # Last parameter is a waiting time
            fileThreads[createdFileName].start()
            
        elif event.event_type == 'moved':
            # Stop Thread and clean object from Dictionary
            print("A file has been moved to another directory")
            
class dogThread(threading.Thread):
    def __init__(self, threadID, threadName, fileName, delay):
        """
        threadID - Is the Thread identifier, defined as an integer, each thread should be different.
        threadFileName - Is the name of the file containing the matador.log path defined as 
            the absolute path to this file.
        counter - Is a delay time defined in seconds for the thread execution process.
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName # This attribute refers to the file to be read and the thread name
        self.fileName = fileName
        self.delay = delay
        self.exitFlag = 0
        self.matador = "matador.log"
        self.apcFiles = None
        self.optParameters = None
        self.bestSolution = None
        
        # Custom Class Attributes
        self.isRunningOptimization = True
        # self.threadMaxLifeTime = 7200 # Int Value represents seconds
        self.threadMaxLifeTime = 30 # Int Value represents seconds
        
    def run(self):
        print("Starting :", self.name)
        self.completedWatcher(self.fileName, self.delay)
        print("Exiting :", self.name)
            
    def completedWatcher(self, threadName, delay):
        """
        This method will check for changes in matador.log file.
        If the file has a flag, or string such as
                Complete execution time
        This string alerts that the optimization job has been
        completed and it can be processed.
        This process will check for the string every X time
        while thread is alive.
        The max life time for each thread will be of 7,200 sec (2hrs),
        if the Optimization Job is not completed
        """
        runningThread = True
        threadCurrentTime = 0
        self.apcFiles, self.optParameters = self.readOptFile(threadName) # Reads matador.log path in consequent file (Created in CARMDATA by opt)
        print("SubPlan Optimizations path: %s" % self.apcFiles)
        print("SubPlan Filter Parameter: %s" % self.optParameters)
        """
        TODO <OK>: Send 2nd line in file to another Script.
        Lines possibly received:
            - ALL_WITH_BIDS
            - 00001122,00001123,00001124,00001125,00001126
            
        TODO <OK>: Use Case -> What is an Optimization job does never finish? D: Default: ----Do Nothing---- NTH[Clean Objects]
        Ultra Nice To Have - IF (Sobrepasa max exec time) THEN (Warning Email: Opt Job was not completed [Send Path])
        Moves file to error/ includes timestamp
        """
        while runningThread and threadCurrentTime <= self.threadMaxLifeTime:
            # Function that reads file in search for 'completed'
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Search in file (%s): %s" %(threadName, time.ctime(time.time())))
            print("Elapsed time: %s seconds" % threadCurrentTime)
            runningThread = self.readMatador(self.apcFiles)
            if runningThread:
                time.sleep(delay)
                threadCurrentTime += delay
                
        if threadCurrentTime >= self.threadMaxLifeTime:
            print("Optimization could not be completed")
            # NTH Send Warning E-mail
            self.moveToDir("error")
            
    def readMatador(self, filePath):
        """
        This function reade the file content in search of a 
        'completed execution time' string 
        """
        filePath = os.path.join(filePath, self.matador)
        print("--> Reading file: %s" % filePath)
        matadorFile = open(filePath, "r")
        matadorFile = matadorFile.readlines()[-5:]
        
        for line in matadorFile:
            if "Complete execution time" in line:
                # TODO: Call report Generation (Send matador path 203)
                print("Optimization has been completed!!")
                # TODO: Concatenate 'best_solution' to received Path symlink and resolve for AbsPath to get real Best Solution
                
                curr_path_elemts = os.path.dirname(__file__).split('/')
                carmusr = '/'.join(curr_path_elemts[0:len(curr_path_elemts)-5])
                binDirectory = os.path.join(carmusr,"bin")
                commandString = carmusr + "lib/python/carmusr/crew_modules/bid/max_roster_report.py -crew = %s -solution = %s" % (self.optParameters, "best_solution_path")
                os.system(os.path.join(binDirectory,'run_crew_modules_headless.sh --command=%s'%commandString))
                self.isRunningOptimization = False
                self.moveToDir("archive")
                break
                # TODO<OK>: Send consequent file to [CARMDATA]/pbs_opt_info/archive/[timestamp_name].txt
                #   NOTE: Add the [TimeStamp] when moving file to archive/
        """
        If the string 'Completed execution time' is in any of the lines, then the SubPlan Optimization
        has been completed and the file can be processed.
        """
        return self.isRunningOptimization
            
    def readOptFile(self, fileName):
        """
        Main file, contains information about the path where the matador.log 
        is inside an specific SubPlan, this function will only read that line,
        then returns that path as an string.
        This is an example of the path contained into the CARMDATA:
        [CARMDATA]/
            LOCAL_PLAN/
                [timetable]/
                    [version]/
                        [LocalPlan]/
                            [SubPlan]/
                                APC_FILES
        The expected path should at least contain up to APC_FILES directory.
        This String does not contain the '/' at the end.
        To giver the exact path to the Matador file, the string 'Matador.log' should
        be concatenated at the end.
        The received path could be used in another variables, so consider to give these
        values as an assignment to the object attributes.
        """
        # TODO <OK>: Received path will be received up to APC_FILES/
        #   NOTE: Check for a 2nd line received in file
        #   NOTE: Append matador.log file name to use the matador file
        file = open(fileName, "r")
        matadorPath = file.readline().strip('\n')
        optParameter = file.readline().strip('\n')
        
        print("Matador Path: ", matadorPath)
        print("Found SubPlan Parameter: ", optParameter)
        
        return (matadorPath, optParameter)
    
    def moveToDir(self, directory):
        # The file should be moved when Optimization Job has been completed
        # TODO<OK>: Segregate file by year-month -> YYYYMM
        timestamp = datetime.now().strftime('%Y%m%d_%H%M_%S%f')
        periodDirectory = datetime.now().strftime('%Y%m')
        archivePath, fileName = os.path.split(self.fileName)
        archivePath = os.path.join(archivePath, directory)
        newFileName = timestamp + "_" + fileName
        periodDirectory = os.path.join(archivePath, periodDirectory)
        if not os.path.exists(periodDirectory):
            os.makedirs(periodDirectory)
            
        if not os.path.exists(archivePath):
            os.makedirs(archivePath)
            
        destination = os.path.join(archivePath, periodDirectory, newFileName)
        shutil.move(self.fileName, destination)
        print("Optimzation File has been moved: ", destination)
        
            
        
if __name__ == "__main__":
    guardog().main("C:/Git/python-watchdog-multithread")
    # (sys.argv[1]) <--- CARMDATA
    # C:/Git/python-watchdog-multithread/ == [CARMDATA]
    """
    kill_command = "pkill -9 -f email_notifications.py"
    start_command = "%s/lib/python/carmusr/crew_modules/request/email_notifications.py %s &"%(carmusr,carmusr)
    
    
    Expected SubPlan Path:
    /carm/implementation/project/LANPB/data/SSC_Data/LOCAL_PLAN/LIVECLLH/202107/CABLA_MERGED_v4/0.MAX_ROSTER_auto/APC_FILES
    /opt/Jeppesen/share/latam/usr/dev/
    
    """
    
        