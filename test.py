# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 10:11:57 2015

@author: brian
"""

#from routing import kosaraju
#kosaraju.test_clean_graph()

#from analysis import analyse_trip_times

#analyse_trip_times.analyse_trip_locations()

#from traffic_estimation import bug_test
#bug_test.run_test()


#from analysis import plot_link_speeds
#plot_link_speeds.make_video('analysis/vid_tmp', 'analysis/someweek')

from traffic_estimation.plot_estimates import make_video, restore_video
from datetime import datetime, timedelta
#make_video("tmp_video", "unknown_vid", dates=[datetime(2011,9,18) + timedelta(hours=1)*x for x in range(168)])
#make_video("typical_video", "typical_vid", dates=[datetime(2011,3,9) + timedelta(hours=1)*x for x in range(24)])



from routing.partition_graph import run_many_tests, simple_test, delete_new_jersey, run_many_tests_spectral, plot_test
#plot_test()
#delete_new_jersey()


#restore_video("tmp_vid", "tmp_vid", "tmp_zscores.pickle")

from traffic_estimation.CV_TrafficEstimation import run_full_day
run_full_day()
