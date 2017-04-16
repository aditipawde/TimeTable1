import main_adi as m
import costFunctions as cf
import math 
import random

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
n_classes = len(classes_tobe_scheduled);
#print(n_classes);

# Create room groups -- used in cost claculations and final room allocation
lab_group = []
theory_group = []

m.get_room_groups(lab_group, theory_group);
max_theory = len(theory_group);
max_lab = len(lab_group);

# Select initial solution
tt_initial = m.generate_random_tt(req_all, n_days, n_slots, n_lec_per_slot, n_classes);
#print(tt_initial[2,:,:,:])

n_repetitions = 10;
temperature = 50;
cooling_rate = 0.8;


while (temperature > 1):

    i = 0
    while (i < n_repetitions):

        # Get new timetable in which requirements have moved
        tt_new = m.swap_neighbourhood(tt_initial, req_all, n_days, n_slots, n_lec_per_slot);


        # Calculate cost difference
        cost = cf.get_cost(tt_new, req_all, n_days, n_slots, max_theory, max_lab) - cf.get_cost(tt_initial, req_all, n_days, n_slots, max_theory, max_lab);

        # If cost of new time table is less, accept it
        if (cost <= 0 or (math.exp(-1 * cost / temperature) < random.random())):
            tt_initial = tt_new;

        i += 1

    temperature = cooling_rate * temperature;

