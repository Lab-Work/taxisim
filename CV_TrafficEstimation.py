# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 18:28:54 2014

@author: brian
"""
from TrafficEstimation import *
from random import shuffle
from multiprocessing import Pool

# Splits a list into a training set and a test set
# Params:
    # full_data - a list of Trips.  Should already be shuffled
    # fold_id - the fold to be evaluated (should be less than num_folds)
    # num_folds - the 
def split_train_test(full_data, fold_id, num_folds):
    start_id = int(len(full_data) * float(fold_id) / num_folds)
    end_id = int(len(full_data) * float(fold_id+1) / num_folds)

    
    test = full_data[start_id:end_id]
    train = full_data[:start_id] + full_data[end_id:]
    return train, test
    


def run_fold((shuffled_trips, nodes_fn, links_fn, fold_id, num_folds)):

    print("Running fold " + str(fold_id))
    road_map = Map(nodes_fn, links_fn)
    train, test = split_train_test(shuffled_trips, fold_id, num_folds)    
    
    print("Estimating travel time " + str(fold_id))
    (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors) = estimate_travel_times(
        road_map, train, max_iter=20, test_set=test)
    
    
    test = [trip for trip in test if trip.dup_times != None]
    train = [trip for trip in train if trip.dup_times != None]    
    
    print(len(test))
    print(len(train))
    
    #We have to reset these fields so the objects can be pickled/returned across processes
    for trip_lst in [test, train]:
        for trip in trip_lst:
            trip.origin_node = None
            trip.dest_node = None
            trip.path_links = None
    
    
    return (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test)

def fold_iterator(full_data, nodes_fn, links_fn, num_folds):
    for i in range(num_folds):
        yield (full_data, nodes_fn, links_fn, i, num_folds)


def avg_lists(list_of_lists):
    output_size = max(map(len, list_of_lists))
    sums = [0.0] * output_size
    counts = [0.0] * output_size

    for lst in list_of_lists:
        for i in range(len(lst)):
            sums[i] += lst[i]
            counts[i] += 1
    
    avgs = [sums[i] / counts[i] for i in range(output_size)]
    return avgs


def combine_outputs(output_list):
    train_avg = avg_lists([iter_avg_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    train_perc = avg_lists([iter_perc_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    test_avg = avg_lists([test_avg_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    test_perc = avg_lists([test_perc_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    
    train_set = [trip for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list for trip in train]
    test_set = [trip for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list for trip in test]
    
    return (train_avg, train_perc, test_avg, test_perc, train_set, test_set)
    

def perform_cv(full_data, nodes_fn, links_fn, num_folds, num_cpus = 1):
    from matplotlib import pyplot as plt
    shuffle(full_data)

    it = fold_iterator(full_data, nodes_fn, links_fn, num_folds)
    pool = Pool(num_cpus)
    output_list = pool.map(run_fold, it)
    (train_avg, train_perc, test_avg, test_perc, train_set, test_set) = combine_outputs(output_list)
    
    #Generate figures
    plt.cla()
    plt.plot(train_avg)
    plt.plot(test_avg)
    plt.legend(["Train", "Test"])
    plt.xlabel("Iteration")
    plt.ylabel("Avg Absolute Error (seconds/trip)")
    plt.savefig("avg_error.png")
    
    plt.cla()
    plt.plot(train_perc)
    plt.plot(test_perc)
    plt.legend(["Train", "Test"])
    plt.xlabel("Iteration")
    plt.ylabel("Avg Relative Error")
    plt.savefig("perc_error.png")
    
    plt.cla()
    plt.scatter([trip.time for trip in train_set], [trip.estimated_time for trip in train_set], color="blue")
    plt.scatter([trip.time for trip in test_set], [trip.estimated_time for trip in test_set], color="red")
    plt.xlabel("True Time")
    plt.ylabel("Estimated Time")
    plt.legend(["Train", "Test"])
    plt.savefig("time_scatter.png")
    
    plt.cla()
    plt.plot(sorted([abs(trip.time-trip.estimated_time) for trip in train_set]))
    plt.plot(sorted([abs(trip.time-trip.estimated_time) for trip in test_set]))
    plt.xlabel("Trip Rank")
    plt.ylabel("Absolute Error")
    plt.legend(["Train", "Test"])
    plt.savefig("abs_error_sorted.png")
    
    plt.cla()
    plt.plot(sorted([abs(trip.time-trip.estimated_time)/trip.time for trip in train_set]))
    plt.plot(sorted([abs(trip.time-trip.estimated_time)/trip.time for trip in test_set]))
    plt.legend(["Train", "Test"])
    plt.xlabel("Trip Rank")
    plt.ylabel("Percent Error")
    plt.savefig("perc_error_sorted.png")
    
    


if(__name__=="__main__"):
    #print("Loading trips")
    trips = load_trips("sample_2.csv", 20000)
    #print("We have " + str(len(trips)) + " trips")
    
    #print("Loading map")

    
    perform_cv(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 8, num_cpus=8)
    print("Done!")
    





    