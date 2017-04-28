#
# This module handles swapping and realated functions of required for SA
# 
import init_random_timetable as m
import costFunctions as cf
import math 
import random
import dataAccessSQLAlchemy as da
import numpy as np



def get_overlapping_batch_list (f_overlapping_batches_with_classId, classId, batchId):
    "Gives overlapping batches for a class for a batchId"

    # Filter where clasId and overlapClassId are same 
    f_overlapping_batches_classId = f_overlapping_batches_with_classId[(f_overlapping_batches_with_classId['classId'] == classId) & (f_overlapping_batches_with_classId['overlapClassId'] == classId) & (f_overlapping_batches_with_classId['batchId'] == batchId)]

    overlapping_batch_list = f_overlapping_batches_classId.drop('classId', axis=1)
    overlapping_batch_list = overlapping_batch_list.drop('overlapClassId', axis=1).values.tolist()

    # Create batch set - union of all lists, remove given batch
    overlap_set = set().union(*overlapping_batch_list);
    #overlap_set = overlap_set - {batchId}

    batch_list = list();

    for item in overlap_set:
        batch_list.append(item);

    return batch_list;

def is_only_theory (tt_vector, req_id):
    "Checks if the theory class is the only occuring for all subslots. Req_id here is a theory requirement id"
    
    # Flag for checking the only theory condition
    not_the_only = 1

    for i in range (len(tt_vector)):
        if (not np.isnan(tt_vector[i]) and tt_vector[i] != req_id):
            not_the_only = 0;

    return not_the_only;
   
def find_random_theory_empty_slot (tt, classId, n_days, n_slots):
    "Finds random empty slot for theory" 
    
    # Number of tries for attempting to find empty slot
    max_tries = n_days * n_slots;

    # Select random day and slot check if all lectures in it are empty
    while (max_tries > 0):
        r_day = random.randint (0, n_days - 1);
        r_slot = random.randint (0, n_slots - 1);   

        all_lectures  = tt[classId, r_day, r_slot, :];

        if ((np.isnan(all_lectures)).all()):
            return [r_day, r_slot]

        max_tries -= 1;

    # Retun nan if not found
    if (max_tries == 0):
        return [np.nan, np.nan]

def make_slot_empty (timetable, req_all, classId, req_id, theory_roomgroup, lab_roomgroup):
    "Removes req from the slot/subslots, updates theory_roomgroup and lab_roomgroup accordingly"

    req_category = req_all.loc[req_id, 'category'];

    indices = np.argwhere(timetable[classId] == req_id)

    for i in range(len(indices)):  # Check for all hours

        day, slot, subslot = indices[i];

        timetable[classId, day, slot, subslot] = np.nan

        if (req_all.loc[req_id, 'category'] == 'T'):
            theory_roomgroup[day, slot] = theory_roomgroup[day, slot] - 1 
        else:
            lab_roomgroup[day, slot] = lab_roomgroup[day, slot] - 1 

    return timetable, theory_roomgroup, lab_roomgroup


def separate_theory_lectures(timetable, req_all, classId, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
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
            empty_slot =  find_random_theory_empty_slot(timetable, classId, n_days, n_slots);

            #print ("first empty slot: ",empty_slot);
            if (not ((np.isnan(empty_slot)).all())):
                #timetable[timetable == req] = np.nan;
                #timetable[classId, empty_slot[0], empty_slot[1], 0] = req;

                if (m.is_slot_available(req_all, timetable, classId, empty_slot[0], empty_slot[1], req, theory_roomgroup, lab_roomgroup, max_theory, max_lab)):
                    make_slot_empty (timetable, req_all, classId, req, theory_roomgroup, lab_roomgroup);
                    m.assign(timetable, classId, empty_slot[0], empty_slot[1], req, req_all, theory_roomgroup, lab_roomgroup);
                
        #print(req, req_lectures, req_day, req_slot, isTheOnly, empty_slot);
    return timetable;

def separate_theory_wrapper (timetable, req_all, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
    "Acts as wrapper around separate_theory_lectures"

    for classId in set(req_all.classId):
        separate_theory_lectures(timetable, req_all, classId, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab);
            
def shift_theory_to_empty_slot (timetable, req_all, n_class, n_days, n_slots, class_id, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
    "Shift a theory to empty slot"

    req_theory = req_all.loc[(req_all['classId'] == class_id) & (req_all['category'] == 'T')]
    #req_theory = req_for_given_class.loc[req_for_given_class['category'] == 'T']

    for req in req_theory.index:
        # Get day and slot for a requirement
        indices = np.argwhere (timetable[class_id] == req);
        req_day = indices[0][0];
        req_slot = indices[0][1];

        # Find empty slot
        empty_slot =  find_random_theory_empty_slot(timetable, class_id, n_days, n_slots);

        # Shift to empty slot
        
        if (not ((np.isnan(empty_slot)).all())):
            #timetable[timetable == req] = np.nan;
            #timetable[class_id, empty_slot[0], empty_slot[1], 0] = req;

            if (m.is_slot_available(req_all, timetable, class_id, empty_slot[0], empty_slot[1], req, theory_roomgroup, lab_roomgroup, max_theory, max_lab)):
                make_slot_empty (timetable, req_all, class_id, req, theory_roomgroup, lab_roomgroup);
                m.assign(timetable, class_id, empty_slot[0], empty_slot[1], req, req_all, theory_roomgroup, lab_roomgroup);
            
    return timetable;

def separate_batches (timetable, req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
    "Seaparates batches with same batch id in a slot and batches which cannot overlap"

    # Get from database classId, batchId, overlapClassId, overlapBatchId
    f_overlapping_batches_with_classId = da.execquery("SELECT bc.classId, bc.batchId, bca.classId as 'overlapClassId', bca.batchId as 'overlapBatchId' FROM batchClass bc, batchClass bca, batchCanOverlap bo WHERE bc.batchId = bo.batchId AND bca.batchId = bo.batchOverlapId ");

    n_classes, n_days, n_slots, n_lec_per_slot = timetable.shape;

    for classId in set(req_all.classId):

        # lab requirements for a class
        req_class_lab = req_all[(req_all['category'] == 'L') & (req_all['classId'] == classId)]
        max_tries = len(req_class_lab);

        # Check if requirements are present, there are few cases where this does not satisfy
        if (len(req_class_lab) > 0): 

            while (max_tries > 0):
                # Select 1 lab requirement randomly, take its batchId
                r_req_no = random.choice((req_class_lab.index).tolist()) 

                r_req = req_all[(req_all.index == r_req_no)];
                r_req_batchId = r_req.loc[r_req_no, 'batchId']

                # Get its starting location
                indices = np.argwhere (timetable[classId] == r_req_no);
                r_req_day, r_req_slot, r_req_subslot = indices[0];

                # Get batches which can go parallel
                batches_allowed = get_overlapping_batch_list (f_overlapping_batches_with_classId, classId, r_req_batchId)
                if (len(batches_allowed) > 0):
                    batches_allowed.remove(r_req_batchId);

                # Check for all requirements in this slot if their batchIds are same 
                for i in range(0, n_lec_per_slot):
                    req_no = timetable[classId, r_req_day, r_req_slot, i]

                    if (not np.isnan(req_no)):
                        req = req_all.loc[req_all.index == req_no]
                        req_batchId = req.loc[req_no, 'batchId']

                        if (r_req_no != req_no and (r_req_batchId == req_batchId or (len(batches_allowed) > 0 and (req_batchId not in batches_allowed)))):
                            #print("found for ", r_req_batchId)

                            # Take req indices
                            req_indices = np.argwhere (timetable[classId] == req_no);                            

                            # Selct 1 batch randomly
                            if (len(batches_allowed) > 0):

                                tries = len(req_class_lab);
                                isSuccess = False
                                
                                while ((not isSuccess) and (tries > 0)):
                                    
                                    random_batch = random.choice(batches_allowed);
                                    #isSuccess = False
                                    # Get requirements forrandom batch
                                    req_for_random_batch = req_all[(req_all['batchId'] == random_batch)]

                                    # Choose 1 req randomly, take its starting location
                                    req_test = random.choice((req_for_random_batch.index).tolist());

                                    test_indices = np.argwhere (timetable[classId] == req_test);
                                    test_day, test_slot, test_subslot = test_indices[0];

                                    # Check if there is availability for r_req_no in that slot
                                    is_available = m.is_slot_available(req_all, timetable, classId, test_day, test_slot, r_req_no, theory_roomgroup, lab_roomgroup, max_theory, max_lab);

                                    if (is_available):
                                        make_slot_empty(timetable, req_all, classId, r_req_no, theory_roomgroup, lab_roomgroup)
                                        m.assign(timetable, classId, test_day, test_slot, r_req_no, req_all, theory_roomgroup, lab_roomgroup);
                                        isSuccess = True
                                    tries -= 1
                               
                                        # Remove req from earliear allotment
                                        #for j in range(len(indices)):
                                        #    timetable[classId, indices[j][0], indices[j][1], indices[j][2]] = np.nan

                    else:
                        break;                                

                max_tries -= 1

       
def swap_neighbour(timetable, req_all, n_classes, n_days, n_slots, theory_roomgroup, lab_roomgroup, max_theory, max_lab):
    "Swaps neighbors ot find better timetable"

    # Keep theory lectures as the only lectures
    for classId in set(req_all.classId):
        shift_theory_to_empty_slot(timetable, req_all, n_classes, n_days, n_slots, classId, theory_roomgroup, lab_roomgroup, max_theory, max_lab);

    #print("Before seapaarting bacthes");
    separate_batches(timetable, req_all, theory_roomgroup, lab_roomgroup, max_theory, max_lab);

    return timetable;
