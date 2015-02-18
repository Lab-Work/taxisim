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


from analysis import plot_link_speeds
plot_link_speeds.make_video('analysis/vid_tmp', 'analysis/someweek')