import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np
import costFunctions as cf


# Join requirements for lab batches and theory classes

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



#These values need to be calculated from the database
#n_classes = 14
#n_days = 5
#n_slots = 10
#n_max_lecs_per_slot = 4


def generate_random_tt (req_all, n_days, n_slots, n_lec_per_slot, n_classes):
    "Generates time table where classwise requirements are randomly allocated to days and slots"

    timetable_np = np.empty((n_classes, n_days, n_slots, n_lec_per_slot))*np.nan

    for c in (set(req_all.classId)):    #First take one class
    
        req_for_given_class=req_all.loc[req_all['classId'] == c]      #List all the requirements for that class in req_forgivenclass
 
        #print(set(req_forgivenclass.index))     #These are the indices of the requirements for this class
        for req in set(req_for_given_class.index):    #Schedule each of these requirements
            #print(req)
            req_tuple = req_all.loc[req_all.index == req]
            #print(req_tuple)
            if (req_tuple.iloc[0]['category'] == 'L'):
                not_assigned = 1
                while(not_assigned == 1):      #Keep on scheduling till not found
                    r_day = random.randint(0,n_days-1)
                    r_slot = random.randint(0, n_slots-1)
                    r_lecnumber = random.randint(0,n_lec_per_slot-1)
                    print c
                    print r_day
                    print r_slot
                    print r_lecnumber
                    if(np.isnan(np.sum(timetable_np[c,r_day,r_slot,r_lecnumber]))):   #Check if that slot is empty, this way of using np.isnan is the fastest way of doing so
                        timetable_np[c,r_day,r_slot,r_lecnumber] = req
                        not_assigned = 0
            else:
                not_assigned = 1
                while(not_assigned == 1):      #Keep on scheduling till not found
                    r_day = random.randint(0,n_days-1)
                    r_slot = random.randint(0, n_slots-1)
                    r_lecnumber = 0;
                    if(np.isnan(np.sum(timetable_np[c,r_day,r_slot,:]))):   #Check if that slot is empty, this way of using np.isnan is the fastest way of doing so
                        timetable_np[c,r_day,r_slot,r_lecnumber] = req
                        not_assigned = 0

    return timetable_np;


def get_room_groups(lab_group, theory_group):
    "Forms 2 groups of rooms. lab_group contains rooms with roomCount < 25, all others in theory_group"

    f_room = da.initialize('room');

    for i in range(len(f_room)):
        if (f_room.iloc[i]['roomCount'] > 25):
            theory_group.append(f_room.iloc[i]['roomId']);
        else:
            lab_group.append(f_room.iloc[i]['roomId']);



def swap_neighbourhood (tt, req_all, n_days, n_slots, n_lec_per_slot):
    "Searches neighbourhood for swapping and returns modified timetable"

    max_swaps = 50

    for class_id in set(req_all.classId):

        i = 0
        while(i < max_swaps):

            # Choose 1 slot randomly
            r_day1 = random.randint(0,n_days-1)
            r_slot1 = random.randint(0, n_slots-1)
            r_lecnumber1 = random.randint(0, n_lec_per_slot-1)
            r_isEmpty1 = np.isnan(np.sum(tt[class_id, r_day1, r_slot1, r_lecnumber1]))


            # Choose another slot randomly
            r_day2 = random.randint(0,n_days-1)
            r_slot2 = random.randint(0, n_slots-1)
            r_lecnumber2 = random.randint(0, n_lec_per_slot-1)
            r_isEmpty2 = np.isnan(np.sum(tt[class_id, r_day2, r_slot2, r_lecnumber2]))


            # Slot 1 is empty and 2 is not -- move requirement of 2 to 1
            if (r_isEmpty1 and not r_isEmpty2):
                tt[class_id, r_day1, r_slot1, r_lecnumber1] = tt[class_id, r_day2, r_slot2, r_lecnumber2]
                i += 1

            # Slot 2 is empty and 1 is not -- move requirement of 1 to 2
            if (not r_isEmpty1 and r_isEmpty2):
                tt[class_id, r_day2, r_slot2, r_lecnumber2] = tt[class_id, r_day1, r_slot1, r_lecnumber1]
                i += 1

            # If both are not empty, swap them
            if (not r_isEmpty1 and not r_isEmpty2):
                temp_req =  tt[class_id, r_day1, r_slot1, r_lecnumber1]
                tt[class_id, r_day1, r_slot1, r_lecnumber1] = tt[class_id, r_day2, r_slot2, r_lecnumber2]
                tt[class_id, r_day2, r_slot2, r_lecnumber2] = temp_req
                i += 1

    return tt;





    #print(timetable_np[c,:,:,:])

#print(timetable_np.shape);
#teacher_cost = teacher_overlap(timetable_np)
#print("Teacher cost:")
#print(teacher_cost)



#print(theory_group, len(theory_group));
#print(lab_group, len(lab_group));

#room_cost = cf.get_room_allocation_overflow(timetable_np, req_all, len(theory_group), len(lab_group));


#print("room cost");
#print(room_cost);

