import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np
import costFunctions as cf

def get_all_requirements ():
    "Joins scheduling requirements of theory and lab for all classes"

    ## Get all scheduling requirements -- Join theory and lab requirements

    f_subjectClassTeacher = da.execquery('select s.subjectId, subjectShortName, totalHrs, eachSlot, c.classId, teacherId from subject s, subjectClassTeacher c where s.subjectId = c.subjectId;')
    f_subjectClassTeacher.insert(5,'batchId','-')
    f_subjectClassTeacher.insert(6,'category','T') #T for theory

    f_subjectBatchTeacher = da.execquery('select s.subjectId, subjectShortName, totalHrs, eachSlot, sbt.batchId, bc.classId, teacherId from subject s, subjectBatchTeacher sbt, batchClass bc where s.subjectId = sbt.subjectId AND sbt.batchId = bc.batchId;')
    f_subjectBatchTeacher.insert(6,'category','L') #L for Lab

    f_subjectBatchClassTeacher = pd.concat([f_subjectClassTeacher, f_subjectBatchTeacher])

    ## Split requirements based on each slot

    f_subjectBatchClassTeacher = f_subjectBatchClassTeacher.reset_index();

    totallectures_list = (f_subjectBatchClassTeacher['totalHrs'] / f_subjectBatchClassTeacher['eachSlot'])

    # Create empty dataframe to save all the requirements
    req_all = pd.DataFrame(index=range(int(totallectures_list.sum())), columns=list(f_subjectBatchClassTeacher))
    j = 0

    for i in range(len(req_all)):
        if((f_subjectBatchClassTeacher.iloc[j]['totalHrs']/f_subjectBatchClassTeacher.iloc[j]['eachSlot'])>0):
            req_all.loc[[i]] = f_subjectBatchClassTeacher.iloc[[j]].values
            f_subjectBatchClassTeacher.set_value(j,'totalHrs', f_subjectBatchClassTeacher.loc[j]['totalHrs'] - f_subjectBatchClassTeacher.loc[j]['eachSlot'])

        if (f_subjectBatchClassTeacher.iloc[j]['totalHrs'] == 0):
            j = j + 1

    return req_all;


def isSlotAvailable(req_all, timetable_np, c, r_day, r_slot, r_lecnumber, req_id):
    "Checks if consecutive slots are available for a requirement"

    #If slot is of duration 1
    SlotsAvailable = 0
    SlotRequirement=int(req_all.loc[req_id, 'eachSlot'])

    #print(SlotRequirement)
    for i in range(SlotRequirement): #Fetching how many lectures do we require to slot
        if(np.isnan(np.sum(timetable_np[int(c), r_day, r_slot+i, r_lecnumber]))):  # Check if that slot is empty, this way of using np.isnan is the fastest way of doing so
            req = req_all.loc[req_all.index == req_id]

            if(req.loc[req_id,'category'] == 'T'): 
                cat='L'
            else: 
                cat='T'

            req_list= timetable_np[int(c), r_day, r_slot+i, :]

            #Fetch the requirement records of the selected values
            if(not np.isnan(np.sum(req_list))):
                if(cat in req_all.loc[set(req_list), 'category']):   #Allow only if there is another lecture of same type, or no lecture at all
                    SlotsAvailable = SlotsAvailable+1
            else:
                SlotsAvailable = SlotsAvailable + 1
        else:
            break
    if(SlotsAvailable == SlotRequirement):
        return True
    else:
        return False


def create_random_timetable(n_classes, n_days, n_slots, n_maxlecsperslot, req_all):
    "Creates a timetable where requirements are randomly slotted. Takes care of duration of each requirement"

    timetable_np = np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan

    for c in (set(req_all.classId)):        # First take one class
        
        req_forgivenclass = req_all.loc[req_all['classId'] == c]        # List all the requirements for that class in req_forgivenclass
        # print(req_forgivenclass)
        # print(set(req_forgivenclass.index))     #These are the indices of the requirements for this class

        for req in set(req_forgivenclass.index):  # Schedule each of these requirements
            notassigned = 1
            while (notassigned == 1):  # Keep on scheduling till not found
                r_day = random.randint(0, n_days)
                r_slot = random.randint(0, n_slots)
                #r_lecnumber = next(lec_num for lec_num in n_maxlecsperslot if timetable_np[int(c), r_day, r_slot, lec_num] is None, None)
                if (isSlotAvailable(req_all, timetable_np, c, r_day, r_lecnumber, r_slot, req)):
 #                   timetable_np=assigntimetable_np[int(c), r_day, r_slot, r_lecnumber] = req
                    notassigned = 0
    return timetable_np



def get_room_groups(lab_group, theory_group):
    "Forms 2 groups of rooms. lab_group contains rooms with roomCount < 25, all others in theory_group"

    f_room = da.initialize('room');

    for i in range(len(f_room)):
        if (f_room.iloc[i]['roomCount'] > 25):
            theory_group.append(f_room.iloc[i]['roomId']);
        else:
            lab_group.append(f_room.iloc[i]['roomId']);