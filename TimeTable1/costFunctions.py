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
    print("Teacher cost %d", teacher_cost);

    return teacher_cost



def get_room_allocation_overflow (timetable, req_all, n_days, n_slots,  max_theory, max_lab):
    "Checks for a day and slot, maximum allocations possible for a room"

    room_cost = 0
    for day in range(n_days):
        for slot in range (n_slots):
            temp_array = timetable[:, day, slot, :]
            req_list = []
            #print(temp_array)
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
           
    print("Room cost %d", room_cost);
    return room_cost


def class_batch_overlap(timetable, req_all):
    "Calculates number of times batches of the same class overlap and theory classes of teh same class overlap"

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

                for sub_slot in slot_array:
                    if not np.isnan(sub_slot):

                        req = req_all.loc[req_all.index == sub_slot]

                        if (req.iloc[0]['category'] == 'T'):        # Class clash can be removed
                            class_list.append(req.iloc[0]['classId'])

                        elif req.iloc[0]['category'] == 'L':
                            batch_list.append(req.iloc[0]['batchId'])

                for class_id in class_list:
                    class_cost = class_cost + class_list.count(class_id) - 1

                for batch_id in batch_list:
                    batches_can_overlap = f_batch_can_overlap[f_batch_can_overlap['batchId'] == batch_id]
                    batches = batches_can_overlap['batchOverlapId']
                    #print(batches)
                    for batch in batch_list:
                        batch_cost = batch_cost + batch_list.count(batch_id) - 1

    #print(batch_cost)
    #print(class_cost)
    return (class_cost + batch_cost)


# def teacher_overlap(timetable):
#     teacher_cost = 0
#     n_classes, n_days, n_slots, n_maxlecsperslot=timetable.shape
#     for day in range(n_days):
#         for slot in range (n_slots):
#             temp_array = timetable[:, day, slot, :]
#             teacher_list = []
#             #print(temp_array)
#             for row in temp_array:
#                 for cell in row:
#                     if not np.isnan(cell):
#                         req = req_all.loc[req_all.index == cell]
#                         teacher_list.append(req.iloc[0]['teacherId'])
#             for teacher_id in teacher_list:
#                 if teacher_id is not None:
#                     teacher_cost = teacher_cost + teacher_list.count(teacher_id) - 1
#
#     return teacher_cost
#
#
# def class_batch_overlap(timetable):
#     class_cost = 0
#     batch_cost = 0
#     n_classes, n_days, n_slots, n_maxlecsperslot=timetable.shape
#     for cl in range(n_classes):
#         for day in range(n_days):
#             for slot in range(n_slots):
#                 class_list = []
#                 batch_list = []
#                 slot_array = timetable[cl,day,slot,:]
#                 for sub_slot in slot_array:
#                     if not np.isnan(sub_slot):
#                         req = req_all.loc[req_all.index == sub_slot]
#                         if (req.iloc[0]['category'] == 'T'):
#                             class_list.append(req.iloc[0]['classId'])
#                         elif req.iloc[0]['category'] == 'L':
#                             batch_list.append(req.iloc[0]['batchId'])
#
#                 for class_id in class_list:
#                     class_cost = class_cost + class_list.count(class_id)-1
#
#                 for batch_id in batch_list:
#                     batches_can_overlap = f_batch_can_overlap[f_batch_can_overlap['batchId']==batch_id]
#                     batches = batches_can_overlap['batchOverlapId']
#                     #print(batches)
#                     for batch in batch_list:
#                         batch_cost = batch_cost + batch_list.count(batch_id) - 1
#
#     #print(batch_cost)
#     #print(class_cost)
#     return (class_cost + batch_cost)


def req_missing(timetable, req_all):
    n_classes, n_days, n_slots, n_maxlecsperslot = timetable.shape
    penalty=0
    for c in range(n_classes):
        req_for_c = req_all.loc[req_all['classId'] == c]
        s = np.unique(timetable[c])
        missing = [x for x in req_for_c.index if x not in s]
        penalty=penalty+len(missing)
        if(len(missing)>0):
            print(c, len(missing))
    return penalty

def get_cost(tt, req_all, max_theory, max_lab):
    n_classes, n_days, n_slots, n_maxlecsperslot = tt.shape
    "Calculates all costs for time table"

    # weights
    w_teacher = w_room = w_batch_class = 1;

    # Varoius costs
    c_teacher = teacher_overlap (tt, req_all, n_days, n_slots);
    c_room = get_room_allocation_overflow (tt, req_all, n_days, n_slots, max_theory, max_lab);
    c_batch_class = class_batch_overlap (tt, req_all);
     
    # Actual cost
    cost = w_teacher * c_teacher + w_room * c_room + w_batch_class * c_batch_class;

    return cost;

