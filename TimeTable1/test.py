import common as m
import costFunctions as cf
import math 
import random
import dataAccessSQLAlchemy as da
import numpy as np


def reduce_batch_class_overlap(timetable, req_all, classId):
    "Swaps requirements in such a way that batch-class overlap is minimized"

    # Get theory requirements for a class
    req_for_given_class = req_all.loc[req_all['classId'] == test_class_Id]
    req_th = req_for_given_class.loc[req_for_given_class['category'] == 'T']
    print(req_th, len(req_th))

    for req in req_th.index:
        # Get day and slot for a requirement
        indices = np.argwhere (timetable[classId] == req);
        req_day = indices[0][0];
        req_slot = indices[0][1];
        #req_lectures = timetable[int(classId), req_day, req_slot, :];

        #print(req_lectures, req_day, req_slot);
        #print(req, np.sum(req_lectures, dtype = np.int32));
        ## Check if that requirement is overlapping with any lab
        #if (np.sum(req_lectures,dtype = np.int32) != int(req)):
            
        #    print("clash"); 

        # Not completed


        #for i in 

# Time table parameters - defined by user
n_days = 5
n_slots = 10
n_lec_per_slot = 4

# Chosen classId
test_class_Id = 4

# Get all scheduling requirements
req_all = m.get_all_requirements();
req_th = req_all.loc[req_all['category'] == 'T']
#print(req_th, len(req_th))
req_for_given_class=req_all.loc[req_all['classId'] == test_class_Id]
print("Requiremnets for give class are:")
print(req_for_given_class)

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
tt_initial = m.create_random_timetable (n_classes, n_days, n_slots, n_lec_per_slot, req_all);
print("Initial TT");
print(tt_initial[test_class_Id, :, :, :])

reduce_batch_class_overlap(tt_initial, req_all, test_class_Id)

#print("Initial cost:")
#print(cf.get_cost(tt_initial, req_all, n_days, n_slots, max_theory, max_lab));

#tt_new =m.swap_neighbourhood(tt_initial, req_all, n_days, n_slots, n_lec_per_slot);
#print("Changed TT");
#print(tt_new[2, :, :, :])

#print("Changed cost:")
#print(cf.get_cost(tt_new, req_all, n_days, n_slots, max_theory, max_lab));


#f_batch_can_overlap = da.initialize('batchcanoverlap');
#print(f_batch_can_overlap);


