import dataAccessSQLAlchemy as da
import pandas as pd
import numpy
import random
import numpy as np

#n_classes = 14
#n_days = 5
#n_slots = 10
#n_max_lecs_per_slot = 4


def teacher_overlap(timetable, req_all, n_days, n_slots):
    "Calculates number of teacher overlaps for all days and all slots"

    teacher_cost = 0
    for day in range(n_days):
        for slot in range (n_slots):
            temp_array = timetable[:, day, slot, :]
            teacher_list = []
            #print(temp_array)
            for row in temp_array:
                for cell in row:
                    if not np.isnan(cell):
                        req = req_all.loc[req_all.index == cell]
                        teacher_list.append(req.iloc[0]['teacherId'])
            for teacher_id in teacher_list:
                if teacher_id is not None:
                    teacher_cost = teacher_cost + teacher_list.count(teacher_id) - 1
    

    return teacher_cost



def get_room_allocation_overflow (timetable, req_all, n_days, n_slots,  max_theory, max_lab):
    "Checks for a day and slot, maximum allocations possible for a room"

    room_cost = 0
    for day in range(n_days):
        for slot in range (n_slots):
            temp_array = timetable[:, day, slot, :]
            req_list = []
            for row in temp_array:
                for cell in row:
                    if not np.isnan(cell):
                        req = req_all.loc[req_all.index == cell]
                        #print(req);
                        if (req.iloc[0]['category'] == 'T'):
                            max_theory -= 1
                        else:
                            max_lab -= 1
    #print(max_theory);
    #print(max_lab);
    if (max_theory < 0):
        room_cost = room_cost + -(max_theory)    
    if (max_lab < 0):
        room_cost = room_cost + -(max_lab)   
           
 
    return room_cost


def class_batch_overlap(timetable, req_all):
    """Calculates overlaps for theory classes and (non allowed) overlaps for batches and increments cost accordingly"""

    class_cost = 0
    batch_cost = 0

    n_classes, n_days, n_slots, n_max_lec_per_slot=timetable.shape
    f_batch_can_overlap = da.initialize('batchcanoverlap');

    for cl in range(n_classes):
        for day in range(n_days):
            for slot in range(n_slots):
                class_list = []
                batch_list = []
                slot_array = timetable[cl,day,slot,:]
                # Make 2 lists-class_list having all classes in the sub-slot & batch-list having all batches in sub-slot
                # Classes have category 'T' and Batches have category 'L'
                for sub_slot in slot_array:
                    if not np.isnan(sub_slot):
                        req = req_all.loc[req_all.index == sub_slot]
                        if req.iloc[0]['category'] == 'T':        # Class clash can be removed
                            class_list.append(req.iloc[0]['classId'])
                        elif req.iloc[0]['category'] == 'L':
                            batch_list.append(req.iloc[0]['batchId'])

                # If the same class is repeated in the class_list for the same sub-slot, increment cost
                if len(class_list) > 1 :        # Cost will be incremented only if multiple classes in same sub-slot
                    for class_id in class_list:
                        class_cost = class_cost + class_list.count(class_id) - 1

                if len(batch_list)>1:           # Cost will be incremented only if multiple batches in same sub-slot
                    for batch_id in batch_list:             # In case same batch is slotted more than once in sub slot
                        batch_cost = batch_cost + batch_list.count(batch_id) - 1
                    # 1. Consider first batch in batch_list.
                    # 2. Get all batches that are allowed to overlap
                    # 3. Loop over all batches in batch_list. If any batch does'nt belong to this list, cost incremented
                    batch_id = batch_list[0]
                    batches_can_overlap = f_batch_can_overlap[f_batch_can_overlap['batchId'] == batch_id]
                    batches_all = batches_can_overlap[batches_can_overlap.columns[2:3]] # get batch_can_overlap column
                    batches_all_list = batches_all['batchOverlapId'].tolist()
                    batches_all_list.append(batch_id)
                    for batch in batch_list:
                        if batch not in batches_all_list:
                            batch_cost += 1

    return class_cost + batch_cost

## To be tested

def getting_lunch_break (timetable, n_days, n_slots, n_classes):
    "Checks if a class is getting lunch break"

    lunch_break_cost = 0;

    # Check for all classes if the lunch break is available
    for classId in range (n_classes):
        for day in range(n_days): #this is wrong
            if (not (np.isnan (timetable[classId, day, 4, :]) or np.isnan (timetable[classId, day, 5, :]) or np.isnan (timetable[classId, day, 6, :]))):
                lunch_break_cost += 1;

    return lunch_break_cost;

## To be tested

def subject_on_same_day (timetable, req_all, classId, n_days, n_slots):
    "Finds out if requirements of same subject fall on same day"

    req_classId = req_all.loc[req_all['classId'] == classId]
    subjects = req_classId['subjectId'] 



    print(subjects);


#def get_teacher_workload_cost (timetable, req_all):
#    "Checks if teacher workload is within maxHrs and minHrs"

#    teacher_req = req_all['teacherId' =t]


def get_cost(tt, req_all, n_classes, n_days, n_slots, max_theory, max_lab):
    "Calculates all costs for time table"

    # weights
    w_teacher = w_room = w_batch_class = 1;
    w_lunch_break = 1;

    # Varoius costs
    c_teacher = teacher_overlap (tt, req_all, n_days, n_slots);
    c_room = get_room_allocation_overflow (tt, req_all, n_days, n_slots, max_theory, max_lab);
    c_batch_class = class_batch_overlap (tt, req_all);
    #c_lunch_break = getting_lunch_break(tt, n_days, n_slots, n_classes);
     
    # Actual cost
    cost = w_teacher * c_teacher + w_room * c_room + w_batch_class * c_batch_class;

    # Print costs
    print("Teacher cost: ", c_teacher);
    print("Room cost: ", c_room);
    print("Batch-class overlap cost: ", c_batch_class);
    #print("Lunch break cost: ", c_lunch_break);

    return cost;

