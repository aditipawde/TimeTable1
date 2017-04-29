#
# This module handles SA algorithm
#
import init_random_timetable as r
import sa_functions as sf
import costFunctions as cf
import math 
import random
import numpy as np;

# Time table parameters - defined by user
n_days = 5
n_slots = 10
n_lec_per_slot = 4
n_classes = 14 # can be loaded from DB

def initialize ():
    "Initailizes scheduling requirements and supporting structures"

    req_all = r.get_all_requirements();

    # Create room groups -- used in cost claculations and final room allocation
    lab_group = []
    theory_group = []

    r.get_room_groups(lab_group, theory_group);
    max_theory = len(theory_group);
    max_lab = len(lab_group);

    # Data structure to keep track of max theory and labs happening in a slot
    theory_roomgroup = np.zeros((n_days, n_slots))
    lab_roomgroup = np.zeros((n_days, n_slots))

    return req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab, theory_group, lab_group

def sa (temperature, cooling_rate, tt_initial, req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
    "Performs Simulated Annealing on time table"

    n_classes, n_days, n_slots, n_lec_per_slot = tt_initial.shape
    n_repetitions = 1;

    while (temperature > 1):

        i = 0
        while (i < n_repetitions):

            is_new_accepted = 0;
            is_zero_cost_found = False;

            tt_before = np.copy(tt_initial);
            # Get new timetable in which requirements have moved
            tt_after = sf.swap_neighbour(tt_initial, req_all, n_classes, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab);

            # Calculate cost difference
            before_cost = cf.get_cost(tt_before, req_all, n_classes, n_days, n_slots, max_theory, max_lab);
            after_cost = cf.get_cost(tt_after, req_all, n_classes, n_days, n_slots, max_theory, max_lab);
            cost_difference = after_cost - before_cost;

            final_cost = before_cost;

            # If cost of new time table is less or cost is more but exp (-cost/temerature) < random probablity, accept it else reject it
            if (after_cost == 0):
                final_cost = after_cost;
                tt_initial = tt_after; 
                is_zero_cost_found = True;
                break;

            if (cost_difference <= 0 or (cost_difference > 0 and math.exp(-1 * cost_difference / temperature) < random.random())):
                tt_initial = tt_after;
                final_cost = after_cost;
                is_new_accepted = 1
            else:
                tt_initial = tt_before;
                final_cost = before_cost;

            #print (i, "Before cost: ", before_cost, "\tAfter cost: ", after_cost, "\t Difference: ", cost_difference, "\t is Accepted: ",is_new_accepted);
            i += 1

        if (is_zero_cost_found):
            break;
        temperature = cooling_rate * temperature;
        
    #final_cost = cf.get_cost(tt_initial, req_all, n_classes, n_days, n_slots, max_theory, max_lab);

    return tt_initial, final_cost

def main ():
    "Main execution of the code"

    # Initialize initial requirements
    req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab, theory_group, lab_group = initialize();

    if (len(req_all) < n_classes * n_days * n_slots * n_lec_per_slot):

        print("---- Simulated Annealing for time table creation ----")
        print("Initializing..");

        # Create random time table and perform initial processing
        tt_initial = r.create_random_timetable(n_classes, n_days, n_slots, n_lec_per_slot, req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab);
        sf.separate_theory_wrapper (tt_initial, req_all, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab);
 
        temperature = 10;
        cooling_rate = 0.6;

        tt_final, final_cost = sa (temperature, cooling_rate, tt_initial, req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab);

        print ("Temparature: ", temperature, "Cooling rate: ", cooling_rate, "Final cost: ", final_cost);

        #print(tt_final[:,:,:,:]);

        sf.write_to_timetable_db(tt_final, req_all, theory_group, lab_group)

    else:
        print("Time table cannot be generated due to very high requirements");


main ();
