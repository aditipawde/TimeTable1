import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np

def find_first_nan(vec):
    """return the index of the first occurence of item in vec"""
    for i in xrange(len(vec)):
        if(np.isnan(vec[i])):
            return i
    return -1

def is_slot_available(req_all, timetable_np, c, r_day, r_slot, req_id):
    #If slot is of duration 1
    n_classes, n_days, n_slots, n_maxlecsperslot = timetable_np.shape
    SlotsAvailable = 0
    SlotRequirement=int(req_all.loc[int(req_id), 'eachSlot'])
    #print(SlotRequirement)
    if(n_slots-r_slot < SlotRequirement):
        return False
    else:
        for i in range(SlotRequirement): #Fetching how many lectures do we require to slot
            j = find_first_nan(timetable_np[int(c), r_day, r_slot + i, :])
            if(j==-1):
                break
            else:
                #if(req_all.loc[req_id,'category']=='T'): cat='L'
                #else: cat='T'
                #req_list= timetable_np[int(c), r_day, r_slot+i, :]
                 ##Fetch the requirement records of the selected values
                #if(not np.isnan(np.sum(req_list))):
                    #if(cat in req_all.loc[set(req_list), 'category']):   #Allow only if there is another lecture of same type, or no lecture at all
                SlotsAvailable=SlotsAvailable+1
                #else:
                    #SlotsAvailable = SlotsAvailable + 1

        if(SlotsAvailable==SlotRequirement):
            return True
        else:
            return False


def assign(timetable_np, c, r_day, r_slot, req_id):
    SlotRequirement = int(req_all.loc[req_id, 'eachSlot'])
    for i in range(SlotRequirement):  # Slotting the lecture for given number of hours
        j=find_first_nan(timetable_np[c, r_day, r_slot+i, :])
        timetable_np[c, r_day, r_slot + i, j]=req_id
    return timetable_np



def create_random_timetable(n_classes, n_days, n_slots, n_maxlecsperslot, req_all):
    timetable_np = np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan
    # print(timetable_np)
    for c in (set(req_all.classId)):  # First take one class
        req_forgivenclass = req_all.loc[req_all['classId'] == c]  # List all the requirements for that class in req_forgivenclass
        req_forgivenclass=req_forgivenclass.sort('eachSlot', ascending=False)
        req_set=req_forgivenclass.index
        for i in range(len(req_set)):  # Schedule each of these requirements
            req=req_set[i]
            notassigned = 1
            while (notassigned == 1):  # Keep on scheduling till not found
                r_day = random.randint(0,n_days-1)
                r_slot = random.randint(0,n_slots-1)
 #               r_lecnumber = next(lec_num for lec_num in n_maxlecsperslot if timetable_np[int(c), r_day, r_slot, lec_num] is None, None)
                if (is_slot_available(req_all, timetable_np, c, r_day, r_slot, req)):
                    timetable_np=assign(timetable_np, int(c), r_day, r_slot, req)
                    notassigned = 0
    return timetable_np

print("Welcome");

f_subject_subjectClassTeacher = da.execquery('select s.subjectId, subjectShortName, totalHrs, eachSlot, c.classId, teacherId from subject s, subjectClassTeacher c where s.subjectId = c.subjectId;')
f_subject_subjectClassTeacher.insert(5,'batchId','-')
f_subject_subjectClassTeacher.insert(6,'category','T') #T for theory
f_subject_subjectBatchTeacher = da.execquery('select s.subjectId, subjectShortName, totalHrs, eachSlot, sbt.batchId, bc.classId, teacherId from subject s, subjectBatchTeacher sbt, batchClass bc where s.subjectId = sbt.subjectId AND sbt.batchId = bc.batchId;')
f_subject_subjectBatchTeacher.insert(6,'category','L') #L for Lab
f_subjectBatchClassTeacher = pd.concat([f_subject_subjectClassTeacher, f_subject_subjectBatchTeacher])
f_batch_can_overlap = da.execquery('select batchId, batchOverlapId from batchCanOverlap;')
#print(f_batch_can_overlap)
x = f_subjectBatchClassTeacher
x = x.reset_index()

totallectures_list = (x['totalHrs'] / x['eachSlot'])
# Create empty dataframe to save all the requirements
req_all = pd.DataFrame(index=range(int(totallectures_list.sum())), columns=list(x))
j = 0
for i in range(len(req_all)):
    if((x.iloc[j]['totalHrs']/x.iloc[j]['eachSlot'])>0):
        req_all.loc[[i]] = x.iloc[[j]].values
        x.set_value(j,'totalHrs', x.loc[j]['totalHrs'] - x.loc[j]['eachSlot'])
    if (x.iloc[j]['totalHrs'] == 0):
        j = j + 1

req_all = req_all.rename(columns={'index': 'id'})
#print(req_all)
#These were attempts to convert float values in reqall to int
#req_all[['classId','eachSlot', 'subjectId', 'totalHrs']] = req_all[['classId','eachSlot', 'subjectId', 'totalHrs']].apply(pd.to_numeric)
#req_all=req_all.apply(pd.to_numeric, errors='ignore')

#These values need to be calculated from the database
#tt1=create_random_timetable(n_classes=14, n_days=5, n_slots=10, n_maxlecsperslot=4, req_all=req_all)
