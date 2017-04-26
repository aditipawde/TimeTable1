import common as m
import costFunctions as cf
import math 
import random
import numpy as np;
import test as t;

# Time table parameters - defined by user
n_days = 5
n_slots = 10
n_lec_per_slot = 4

# Get all scheduling requirements
req_all = m.get_all_requirements();
#req_for_given_class=req_all.loc[req_all['classId'] == 2]
#print(req_for_given_class)

# Get number of classes to be scheduled -- may differ from actual number of classes
classes_tobe_scheduled = set(req_all.classId);
#n_classes = len(classes_tobe_scheduled);
n_classes = 14
#print(n_classes);

# Create room groups -- used in cost claculations and final room allocation
lab_group = []
theory_group = []

m.get_room_groups(lab_group, theory_group);
max_theory = len(theory_group);
max_lab = len(lab_group);

# Select initial solution
tt_initial = m.create_random_timetable(n_classes, n_days, n_slots, n_lec_per_slot, req_all);
#print(tt_initial[2,:,:,:])
 
n_repetitions = 10;
temperature = 10;
cooling_rate = 0.6;

print("First cost: ", cf.get_cost(tt_initial, req_all, n_classes, n_days, n_slots, max_theory, max_lab));

t.separate_theory_wrapper (tt_initial, req_all, n_days, n_slots);
print("After separate cost: ", cf.get_cost(tt_initial, req_all, n_classes, n_days, n_slots, max_theory, max_lab));


def sa (temperature, cooling_rate):
    "Performs Simulated Annealing on time table"

    while (temperature > 1):

        i = 0
        while (i < n_repetitions):

            is_new_accepted = 0;

            tt_before = np.copy(tt_initial);
            # Get new timetable in which requirements have moved
            tt_after = t.swap_neighbour(tt_initial, req_all, n_classes, n_days, n_slots);

            # Calculate cost difference
            before_cost = cf.get_cost(tt_before, req_all, n_classes, n_days, n_slots, max_theory, max_lab);
            after_cost = cf.get_cost(tt_after, req_all, n_classes, n_days, n_slots, max_theory, max_lab);
            cost_difference = after_cost - before_cost;

            # If cost of new time table is less or cost is more but exp (-cost/temerature) < random probablity, accept it
            if (cost_difference <= 0 or (cost_difference > 0 and math.exp(-1 * cost_difference / temperature) < random.random())):
                tt_initial = tt_after;
                is_new_accepted = 1
            else:
                tt_initial = tt_before;

            print (i, "Before cost: ", before_cost, "\tAfter cost: ", after_cost, "\t Difference: ", cost_difference, "\t is Accepted: ",is_new_accepted);
            i += 1

        temperature = cooling_rate * temperature;

    return 


test_array = np.zeros([72, 3], dtype = np.float);
i = 0;

for temperature in range(100.0, 800.0, 100):

    for cooling_rate in range(0.1, 0.9, 0.1):
        cost = sa (temperature, cooling_rate);

        test_array[i] = [temperature, cooling_rate, cost];

