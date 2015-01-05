# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 18:28:54 2014

@author: brian
"""
from TrafficEstimation import *
from random import shuffle
from multiprocessing import Pool
from matplotlib import pyplot as plt
import csv








LEARNING_CURVE_SIZES = [5,10,20,30,40,50,100,200,300,400,500,1000,2000,3000,4000,5000,10000,15000]



# Splits a list into a training set and a test set
# Params:
    # full_data - a list of Trips.  Should already be shuffled
    # fold_id - the fold to be evaluated (should be less than num_folds)
    # num_folds - the total number of folds that are being evaluated
# Returns:
    # train_set - a large slice of the list of Trips
    # test_set - a smaller slice of the list of Trips (mutually exclusive)
def split_train_test(full_data, fold_id, num_folds):
    start_id = int(len(full_data) * float(fold_id) / num_folds)
    end_id = int(len(full_data) * float(fold_id+1) / num_folds)

    
    test = full_data[start_id:end_id]
    train = full_data[:start_id] + full_data[end_id:]
    return train, test
    

# Runs a fold in the cross-validation experiment.  This involves learning the
# link-by-link travel times from the training data, then evaluating on the test data.
# Params: Note that this is passed as a single tuple
    # train - a list of Trips, which will be used as the training set
    # test - a list of Trips, which will be used as the test set
    # road_map - a Map object containing the road network.  Should already be flatten()'ed
    # distance_weighting - the method for computing the weight.  see compute_weight()
# Returns:
    # iter_avg_errors - a list of average absolute training errors at each iteration
    # iter_perc_errors - a list of average percent trainingerrors at each iteration
    # test_avg_errors - a list of average absolute test errors at each iteration
    # test_avg_errors - a list of average percent test errors at each iteration
    # train - the modified Trip objects from the train set, now with .estimated_time attribute
        # (may be a subset of input due to duplicates, invalids)
    # train - the modified Trip objects from the test set, now with .estimated_time attribute
        # (may be a subset of input due to duplicates, invalids)
def run_fold((train, test, road_map, distance_weighting, model_idle_time, initial_idle_time)):

    #print("Running fold - " + str(len(train)) + " train vs. " + str(len(test)) + " test " + str(use_distance_weighting))
    # Prepare the map for use
    road_map.unflatten()
       
    
    # Run the traffic estimation algorithm
    (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors) = estimate_travel_times(
        road_map, train, max_iter=20, test_set=test, distance_weighting=distance_weighting,
        model_idle_time=model_idle_time, initial_idle_time=initial_idle_time)
    
    # Remove the trips that were not estimated (duplicates and errors)
    test = [trip for trip in test if trip.dup_times != None]
    train = [trip for trip in train if trip.dup_times != None]    
    
    
    # We have to reset these fields so the objects can be pickled/returned across processes
    # Otherwise we would have to send the whole graph, because of pointers
    for trip_lst in [test, train]:
        for trip in trip_lst:
            trip.origin_node = None
            trip.dest_node = None
            trip.path_links = None
    
    # Return everything
    return (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test)




# Represents one fold in a learning curve experiment
# With a fixed test set, uses incrementally larger training sets and reports the performance
# Params: - the output from fold_iterator()
    # train - a list of trips
    # test - a list of trips
    # road_map - a Map object, can be flattened
    # distance_weighting - see TrafficEstimation.compute_weight()
def run_fold_learning_curve((train, test, road_map, distance_weighting)):
    road_map.unflatten()
    
    
    
    unique_test = road_map.match_trips_to_nodes(test)

    train_avg_errors = []
    test_avg_errors = []
    
    for size in LEARNING_CURVE_SIZES:
        samp_train = train[:size]
        
        d1 = datetime.now()
        print( "Training model of size " + str(len(samp_train))) 
        (iter_avg_errors, iter_perc_errors, _, test_perc_errors) = estimate_travel_times(
            road_map, samp_train, max_iter=20)
        d2 = datetime.now()
        train_avg_error= iter_avg_errors[-1]
        print ("Finished after " + str(d2 - d1))
        print("Testing model of size " + str(len(samp_train)) + " on " + str(len(unique_test)) + " test trips")
        l1_error, test_avg_error, test_perc_error = predict_trip_times(road_map, unique_test,
                                    route=True, proposed=False, max_speed = None)
        d3 = datetime.now()
        print("Finished testing model of size " + str(size) + " after " + str(d3 - d2))
        print((train_avg_error, test_avg_error))        
        print("Estimated idle time : " + str(road_map.idle_link.time))
        
        
        train_avg_errors.append(train_avg_error)
        test_avg_errors.append(test_avg_error)
    
    return train_avg_errors, test_avg_errors
        
        



# Simple iterator, produces inputs for the run_fold function
    # Params:
    # road_map - a Map object containing the road network.
    # distance_weighting - the method for computing the weight.  see compute_weight()
def fold_iterator(full_data, road_map,  num_folds, distance_weighting=None,model_idle_time=False, initial_idle_time=0):
    for i in range(num_folds):
        train, test = split_train_test(full_data, i, num_folds)
        yield (train, test, road_map, distance_weighting, model_idle_time, initial_idle_time)


# Takes a list of list, and produces an average list (by averaging the inner lists)
# Lists don't need to be the same size.  Short lists are treated as missing data at the end
# So they only influence slots where they actually have a value
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

# Combines the outputs from several calls of run_fold().  The errors are averaged across folds
# and raw predictions are concatenated.
def combine_outputs(output_list):
    # Average train/test errors across folds.  This is kind of tedious since they are
    # all lists (error at each iteration)
    train_avg = avg_lists([iter_avg_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    train_perc = avg_lists([iter_perc_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    test_avg = avg_lists([test_avg_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    test_perc = avg_lists([test_perc_errors for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list])
    
    # Concatenate the trips from each training set, test set
    train_set = [trip for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list for trip in train]
    test_set = [trip for (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors, train, test) in output_list for trip in test]
    
    return (train_avg, train_perc, test_avg, test_perc, train_set, test_set)

# Outputs a table, which summarizes the predictions on both the training and test sets
# Params:
    # trips - a list of Trips, which have already run through TrafficEstimation
    # filename - the CSV filename to output the results
def output_trips(trips, filename):
    with open(filename, 'w') as f:
        w = csv.writer(f)
        w.writerow(['from_lat','from_lon','to_lat','to_lon','time','est_time','distance','est_distance'])
        for trip in trips:
            line = [trip.fromLat, trip.fromLon, trip.toLat, trip.toLon, trip.time, trip.estimated_time, trip.dist, trip.estimated_dist]
            w.writerow(line)

# Performs a cross validation experiment, which splits the full_data into several training/test sets,
# uses the training sets to learn the traffic estimates, predicts on the test sets, reports several
# error metrics, and makes some figures.
# Params:
    # full_data - a list of Trip objects
    # nodes_fn - the CSV filename to read the graph's Nodes from
    # links_fn - the CSV filename to read the graph's Links from
    # num_fold - the K in k-fold cross validation
    # num_cpus - Will run this many folds in parallel
    # distance_weighting - the method for computing the weight.  see compute_weight()
def perform_cv(full_data, nodes_fn, links_fn, num_folds, num_cpus = 1, distance_weighting=None, model_idle_time=False, initial_idle_time=0):
    # shuffle(full_data)

    fn_prefix = dw_string(distance_weighting) + "_" + str(model_idle_time) + "_" + str(initial_idle_time)
    print ("Running " + str(fn_prefix) + " on " + str(len(full_data)) + " trips.")


    road_map = Map(nodes_fn, links_fn)
    road_map.flatten()
    it = fold_iterator(full_data, road_map, num_folds, distance_weighting=distance_weighting, model_idle_time=False, initial_idle_time=0)
    pool = Pool(num_cpus)
    output_list = map(run_fold, it)
    (train_avg, train_perc, test_avg, test_perc, train_set, test_set) = combine_outputs(output_list)
    pool.terminate()
    
    
    fn_prefix = dw_string(distance_weighting) + "_" + str(model_idle_time) + "_" + str(initial_idle_time)
    print("outputting " + str(fn_prefix))
    output_trips(train_set, "results/" + fn_prefix + "train_trips.csv")
    output_trips(test_set, "results/" + fn_prefix + "test_trips.csv")
    
    #Generate figures
    plt.cla()
    plt.plot(train_avg)
    plt.plot(test_avg)
    plt.legend(["Train", "Test"])
    plt.xlabel("Iteration")
    plt.ylabel("Avg Absolute Error (seconds/trip)")
    plt.savefig("results/" + fn_prefix + "avg_error.png")
    
    plt.cla()
    plt.plot(train_perc)
    plt.plot(test_perc)
    plt.legend(["Train", "Test"])
    plt.xlabel("Iteration")
    plt.ylabel("Avg Relative Error")
    plt.savefig("results/" + fn_prefix + "perc_error.png")
    
    plt.cla()
    plt.scatter([trip.time for trip in train_set], [trip.estimated_time for trip in train_set], color="blue")
    plt.scatter([trip.time for trip in test_set], [trip.estimated_time for trip in test_set], color="red")
    plt.xlabel("True Time")
    plt.ylabel("Estimated Time")
    plt.legend(["Train", "Test"])
    plt.savefig("results/" + fn_prefix + "time_scatter.png")
    
    plt.cla()
    plt.plot(sorted([abs(trip.time-trip.estimated_time) for trip in train_set]))
    plt.plot(sorted([abs(trip.time-trip.estimated_time) for trip in test_set]))
    plt.xlabel("Trip Rank")
    plt.ylabel("Absolute Error")
    plt.legend(["Train", "Test"])
    plt.savefig("results/" + fn_prefix + "abs_error_sorted.png")
    
    plt.cla()
    plt.plot(sorted([abs(trip.time-trip.estimated_time)/trip.time for trip in train_set]))
    plt.plot(sorted([abs(trip.time-trip.estimated_time)/trip.time for trip in test_set]))
    plt.legend(["Train", "Test"])
    plt.xlabel("Trip Rank")
    plt.ylabel("Percent Error")
    plt.savefig("results/" + fn_prefix + "perc_error_sorted.png")
    
    print("Average train error = " + str(train_avg[-1]))
    print("Average test error = " + str(test_avg[-1]))
    


def try_idle_times(full_data, nodes_fn, links_fn, num_folds, num_cpus):
    perform_cv(full_data, nodes_fn, links_fn, num_folds, num_cpus = 8, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
    for idle_time in [0,100,200,300,400,500]:
        perform_cv(full_data, nodes_fn, links_fn, num_folds, num_cpus = 8, distance_weighting=None, model_idle_time=True, initial_idle_time=idle_time)

        




# An iterator which downsamples the training set, using more data in each iteration
# Params:
    # train - a list of Trips
    # test - a list of Trips
    # num_slices - the number of different training set sizes to use
    # nodes_fn - the CSV filename to read Nodes from
    # links_fn - the CSV filename to read LInks from
def downsample_iterator(train, test, num_slices, nodes_fn, links_fn):
    for i in range(num_slices):
        cutoff_id = int(float(i+1) * len(train) / num_slices)
        yield (train[:cutoff_id], test, nodes_fn, links_fn)
    



def combine_learning_curves(output_list):
    full_train_err_list = [0]*len(LEARNING_CURVE_SIZES)
    full_test_err_list = [0]*len(LEARNING_CURVE_SIZES)
    
    for train_err_list, test_err_list in output_list:

        for i in range(len(LEARNING_CURVE_SIZES)):
            full_train_err_list[i] += train_err_list[i]
            full_test_err_list[i] += test_err_list[i]
    
    for i in range(len(LEARNING_CURVE_SIZES)):
        full_train_err_list[i] /= len(output_list)
        full_test_err_list[i] /= len(output_list)

    return full_train_err_list, full_test_err_list

# Generates a learning curve, using various sizes of training sets, and ploting the error
# Params:
    # full_data - a list of Trips
    # nodes_fn - the CSV filename to read Nodes from
    # links_fn - the CSV filename to read LInks from
    # num_folds - the K in k-fold cross validation.  REsults will be averaged across folds
    # num_cpus - the folds can be run in parallel on this many processors
def perform_learning_curve(full_data, nodes_fn, links_fn, num_folds, num_cpus = 1, distance_weighting=None):
    shuffle(full_data)
    
    
    road_map = Map(nodes_fn, links_fn)
    road_map.flatten()
    it = fold_iterator(full_data, road_map, num_folds, distance_weighting=distance_weighting)
    
    pool = Pool(num_cpus)
    output_list = pool.map(run_fold_learning_curve, it)
    pool.terminate()

    train_curve, test_curve = combine_learning_curves(output_list)
    
    plt.cla()
    plt.plot(LEARNING_CURVE_SIZES, train_curve)
    plt.plot(LEARNING_CURVE_SIZES, test_curve)
    plt.legend(["Train", "Test"])
    plt.xlabel("Training Set Size")
    plt.ylabel("Avg Absolute Error (seconds/trip)")
    plt.savefig("learning_curve_idle.png")
    
    print("Done!")
 


def dw_string(distance_weighting):
    if(distance_weighting==None):
        return "NONE"
        
    (val_type, kern_type, dist_bw) = distance_weighting
    if(val_type==DW_ABS):
        s = "ABS"
    else:
        s = "REL"
    
    if(kern_type==DW_GAUSS):
        s += "_GAUSS_"
    elif(kern_type==DW_LASSO):
        s += "_LASSO_"
    else:
        s += "_THRESH_"

    s += str(dist_bw)
    
    return s





def try_many_kernels():
    print("Loading trips")
    trips = load_trips("sample_2.csv", 20000)
    shuffle(trips)
    #print("We have " + str(len(trips)) + " trips")
    
    #print("Loading map")

    
    for val_type in [DW_ABS, DW_REL]:
        for kern_type in [DW_GAUSS, DW_LASSO, DW_THRESH]:
            if(val_type==DW_ABS):
                bandwidths = [1600,800,600,400,200,100,50,25,10]
            else:
                bandwidths = [.1, .2, .3, .4, .5, .1, .15, .2,.25, .3, .5]
                
            for dist_bw in bandwidths:
                print("Performing distance weighting " + dw_string((val_type, kern_type, dist_bw)))
                d1 = datetime.now()
                perform_cv(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 8, num_cpus=8, distance_weighting=(val_type, kern_type, dist_bw))    
            
                #perform_learning_curve(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 24, num_folds=8, num_cpus=8)
                d2 = datetime.now()
                print("Done!")
                print(d2 - d1)    
                #perform_cv(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 8, num_cpus=8, use_distance_weighting=False)



if(__name__=="__main__"):
    print("Loading trips")
    trips = load_trips("sample_2.csv", 20000)
    #perform_learning_curve(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 8, num_cpus=8, distance_weighting=None)
    try_idle_times(trips, "nyc_map4/nodes.csv", "nyc_map4/links.csv", 8, num_cpus=8)


    