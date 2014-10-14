from datetime import datetime, timedelta
from multiprocessing import process
from time import sleep

import MITSpeedAlgorithm

# 2011-05-08

start_time = datetime.now()


class ParseFileProcess(process):
    def __init__(self, direc, dateTime):
        super(ParseFileProcess, self).__init__()
        self.file_to_read = "../data_chron/FOIL2011/trip_05.csv"
        # Directory + weekday (0 = Sunday, 6 = Saturday) + hour (0-23)
        self.path = direc
        self.start_time = dateTime
        print dateTime
        self.end_time = dateTime + (
            timedelta(hours=1) - timedelta(microseconds=1))
        filename = tmp_dir + "/" + str((dateTime.weekday() + 1) % 7) + "_" + (
            str(dateTime.hour))
        print filename
        self.file_to_write = filename

    # Run when start is called
    def run(self):
        print "Running"
        MITSpeedAlgorithm(self.file_to_read, self.start_time, self.end_time,
                          self.file_to_write)


tmp_dir = "speeds_per_hour"
# shutil.rmtree(tmp_dir, ignore_errors=True)
# os.mkdir(tmp_dir)

num_pc = 7

workers = [None] * num_pc

# When we know how to end the Simulation
killTime = datetime(year=2011, month=5, day=15)
latest_time = datetime(year=2011, month=5, day=8)

while latest_time < killTime:
    created_job = False
    # Polling - see if any workers are ready to accept a new job
    while(not created_job):
        for i in range(num_pc):
            if(workers[i] is None or not workers[i].is_alive()):
                if workers[i] is not None:
                    workers[i].join()
                latest_time = latest_time + timedelta(hours=1)
                workers[i] = ParseFileProcess(tmp_dir, latest_time)

                # Causes the run file to begin
                workers[i].start()
                created_job = True
                break

        # Sleep for 1 second so the polling doesn't hog a CPU
        if(not created_job):
            sleep(1)
for w in workers:
    if(w is not None and w.is_alive()):
        w.join()
