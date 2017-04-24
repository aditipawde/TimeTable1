import common as m
import costFunctions as cf
import math 
import random
import dataAccessSQLAlchemy as da
import numpy as np


def get_overlapping_batch_list (f_overlapping_batches_with_classId, classId):
    "Gives overlapping batches for a class"
    # Filter where clasId and overlapClassId are same 
    f_overlapping_batches_classId = f_overlapping_batches_with_classId[f_overlapping_batches_with_classId['classId'] == classId]

    f_overlapping_batches_for_classId = f_overlapping_batches_with_classId[f_overlapping_batches_with_classId['overlapClassId'] == classId]


    # Select first batchId, get overlapping batches, convert them to list and append first batchId
    batch_id = f_overlapping_batches_for_classId.iloc[0]['batchId']

    batches_can_overlap = f_overlapping_batches_for_classId[f_overlapping_batches_for_classId['batchId'] == batch_id]
    batches_all = batches_can_overlap[batches_can_overlap.columns[3:4]] # get batch_can_overlap column
    batches_all_list = batches_all['overlapBatchId'].tolist()
    batches_all_list.append(batch_id) # Overlapping batches for a class -- there could be others which can not overlap

    print(batches_all_list);

    return batches_all_list;

def get_req_for_class_category (req_all, classId, category):
    "Gives requirements as per category = 'L' or 'T'"
    req_for_class = req_all.loc[req_all['classId'] == classId];
    batch_req_for_class = req_for_class.loc[req_for_class['category'] == category]



def create_random_tt_batches_first(req_all, n_classes, n_days, n_slots, n_lec_per_slot):
    """ Creates random timetable with batch allotment first """

    # Timetable array
    timetable_np = np.empty((n_classes, n_days, n_slots, n_lec_per_slot)) * np.nan

    # Theory group and lab group array
    theory_roomgroup = np.zeros((n_days, n_slots))
    lab_roomgroup = np.zeros((n_days, n_slots))

    #test_class_Id = 2;

    # Get from database classId, batchId, overlapClassId, overlapBatchId
    f_overlapping_batches_with_classId = da.execquery("SELECT bc.classId, bc.batchId, bca.classId as 'overlapClassId', bca.batchId as 'overlapBatchId' FROM batchClass bc, batchClass bca, batchCanOverlap bo WHERE bc.batchId = bo.batchId AND bca.batchId = bo.batchOverlapId ");

    for classId in set((req_all.classId)):

        # Get all batch, theory requirements and overlapping batch list
        batch_req = get_req_for_class_category (req_all, classId, 'L');
        #batch_req.sort('eachSlot', ascending = False);

        theory_req = get_req_for_class_category (req_all, classId, 'T');

        overlapping_batch_list = get_overlapping_batch_list (f_overlapping_batches_with_classId, classId);

        # Select a day and slot randomly
        r_day = random.randint(0, n_days - 1);
        r_slot = random.randint(0, n_slots - 1);

        if (overlapping_batch_list):
        
            # Only for overlapping batches
            for batchId in overlapping_batch_list:
                req_for_batch = req_all.loc[req_all['batchId'] == batchId]
                print(req_for_batch)

                req_set = req_for_batch.index

                req = random.choice(req_set);

                print(req_set);
                is_scheduled = req_all.iloc[req]['isScheduled'];
                print(req, '->', is_scheduled);

                timetable_np = m.assign(timetable_np, req_all, classId, r_day, r_slot, req);
                req_all.iloc[req]['isScheduled'] = 1

    return timetable_np;

def is_only_theory (tt_vector, req_id):
    "Checks if the theory class is the only occuring for all subslots. Req_id here is a theory requirement id"
    
    # Flag for checking the only theory condition
    not_the_only = 1

    for i in range (len(tt_vector)):
        if (not np.isnan(tt_vector[i]) and tt_vector[i] != req_id):
            not_the_only = 0;

    return not_the_only;

def find_empty_slot_for_class (tt, classId, n_days, n_slots):
    "Finds empty slot for a class"

    for day in range (n_days):
        for slot in range (n_slots):

            found = 1;
            all_lectures  = tt[classId, day, slot, :];

            for i in range (len(all_lectures)):

                if (not np.isnan(all_lectures[i])):
                    found = 0;
                    break;

            if (found == 1):
                return [day, slot];
      
    if (found == 0):
       return [np.nan, np.nan];      


def separate_theory_lectures(timetable, req_all, classId, n_days, n_slots):
    "Swaps requirements in such a way that batch-class overlap is minimized"

    # Get theory requirements for a class
    req_for_given_class = req_all.loc[req_all['classId'] == classId]
    req_th = req_for_given_class.loc[req_for_given_class['category'] == 'T']
    #print(req_th, len(req_th))

    for req in req_th.index:
        # Get day and slot for a requirement
        indices = np.argwhere (timetable[classId] == req);
        req_day = indices[0][0];
        req_slot = indices[0][1];
        req_lectures = timetable[int(classId), req_day, req_slot, :];

        # Check if theory requirement is the only requirement
        isTheOnly = is_only_theory (req_lectures, req);
        
        empty_slot = np.nan;
        
        # Find an empty slot, make earlier location nan and new location to empty slot
        if (not is_only_theory(req_lectures, req)):
            empty_slot =  find_empty_slot_for_class(timetable, classId, n_days, n_slots);

            #print ("first empty slot: ",empty_slot);
            timetable[timetable == req] = np.nan;
            timetable[classId, empty_slot[0], empty_slot[1], 0] = req;
        #print(req, req_lectures, req_day, req_slot, isTheOnly, empty_slot);
    return timetable;
            


       
def swap_neighbor(timetable, req_all, n_class, n_days, n_slots):
    "Swaps neighbors ot find better timetable"

    # Keep theory lectures as the only lectures
    for classId in range(2, n_class):

        separate_thoery_lectures (timetable, req_all, classId, n_days, n_slots);

    return timetable;


# Time table parameters - defined by user
n_days = 5
n_slots = 10
n_lec_per_slot = 4
n_classes = 14

# Chosen classId
test_class_Id = 2

# Get all scheduling requirements
req_all = m.get_all_requirements();
print(req_all)



timetable = create_random_tt_batches_first(req_all, n_classes,n_days,n_slots, n_lec_per_slot);
print(timetable[test_class_Id, :, :, :])


#req_th = req_all.loc[req_all['category'] == 'T']
##print(req_th, len(req_th))
#req_for_given_class=req_all.loc[req_all['classId'] == test_class_Id]
#print("Requiremnets for give class are:")
#print(req_for_given_class)

## Get number of classes to be scheduled -- may differ from actual number of classes
#classes_tobe_scheduled = set(req_all.classId);
##n_classes = len(classes_tobe_scheduled);

##print(n_classes);

## Create room groups -- used in cost claculations and final room allocation
#lab_group = []
#theory_group = []

#m.get_room_groups(lab_group, theory_group);
#max_theory = len(theory_group);
#max_lab = len(lab_group);

## Select initial solution
#tt_initial = m.create_random_timetable (n_classes, n_days, n_slots, n_lec_per_slot, req_all);
#print("Initial TT");



#print("Initial cost:")
#print(cf.get_cost(tt_initial, req_all, n_classes, n_days, n_slots, max_theory, max_lab));

##new_tt = reduce_batch_class_overlap(tt_initial, req_all, test_class_Id, n_days, n_slots)
#new_tt = swap_neighbor (tt_initial, req_all, n_classes, n_days, n_slots);

#print("New TT");
#print(new_tt[test_class_Id, :, :, :])

#print("New cost:")
#print(cf.get_cost(new_tt, req_all, n_classes, n_days, n_slots, max_theory, max_lab));

#nn = cf.subject_on_same_day (new_tt, req_all, test_class_Id,  n_days, n_slots);


#tt_new =m.swap_neighbourhood(tt_initial, req_all, n_days, n_slots, n_lec_per_slot);
#print("Changed TT");
#print(tt_new[2, :, :, :])

#print("Changed cost:")
#print(cf.get_cost(tt_new, req_all, n_days, n_slots, max_theory, max_lab));


#f_batch_can_overlap = da.initialize('batchcanoverlap');
#print(f_batch_can_overlap);


