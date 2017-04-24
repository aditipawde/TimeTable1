import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np
max_theory_roomgroup=10
max_lab_roomgroup=10

def find_first_nan(vec):
    """return the index of the first occurence of item in vec"""
    for i in xrange(len(vec)):
        if(np.isnan(vec[i])):
            return i
    return -1

def get_groups_of_batches(f_batch_can_overlap):
    lists = (f_batch_can_overlap.drop('bo', axis=1)).values.tolist()
    resultslist = []  # Create the empty result list.

    if len(lists) >= 1:  # If your list is empty then you dont need to do anything.
        resultlist = [lists[0]]  # Add the first item to your resultset
        if len(lists) > 1:  # If there is only one list in your list then you dont need to do anything.
            for l in lists[1:]:  # Loop through lists starting at list 1
                listset = set(l)  # Turn you list into a set
                merged = False  # Trigger
                for index in range(len(resultlist)):  # Use indexes of the list for speed.
                    rset = set(resultlist[index])  # Get list from you resultset as a set
                    if len(
                                    listset & rset) != 0:  # If listset and rset have a common value then the len will be greater than 1
                        resultlist[index] = list(
                            listset | rset)  # Update the resultlist with the updated union of listset and rset
                        merged = True  # Turn trigger to True
                        break  # Because you found a match there is no need to continue the for loop.
                if not merged:  # If there was no match then add the list to the resultset, so it doesnt get left out.
                    resultlist.append(l)
    return resultlist

def is_slot_available(req_all, timetable_np, c, r_day, r_slot, req_id, theory_roomgroup, lab_roomgroup):
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
            #Condition 1: Check if consecutive lectures are available
            if(j==-1):
                return False
            #Condition 2: Check if rooms are available
            if (req_all.loc[req_id, 'category'] == 'T'):
                #Check room group availability
                if(theory_roomgroup[r_day, r_slot]>=max_theory_roomgroup):
                    return False
            else: #i.e. category==L
                #Check room group availability
                if(lab_roomgroup[r_day, r_slot]>=max_lab_roomgroup):
                    return False
            #
            # #Condition 3: Check if the parallel lecture is T/L. No T-L or L-T lectures can take place parallely
            # if(req_all.loc[req_id,'category']=='T'): cat_not_allowed='L'
            # else: cat_not_allowed='T'
            # req_list= timetable_np[int(c), r_day, r_slot+i, :]  #Fetch the requirement records of the selected values
            # if(not np.isnan(np.sum(req_list))):
            #     if(cat_not_allowed in req_all.loc[set(req_list), 'category']):   #Allow only if there is another lecture of same type, or no lecture at all
            #         return False
            #     else:
            #         SlotsAvailable = SlotsAvailable + 1
            SlotsAvailable = SlotsAvailable + 1

        if(SlotsAvailable==SlotRequirement):
            return True
        else:
            return False

def assign(timetable_np, c, r_day, r_slot, req_id, req_all, theory_roomgroup, lab_roomgroup):
    SlotRequirement = int(req_single.loc[req_id, 'eachSlot'])
    for i in range(SlotRequirement):  # Slotting the lecture for given number of hours
        j=find_first_nan(timetable_np[c, r_day, r_slot+i, :])
        timetable_np[c, r_day, r_slot + i, j]=req_id
        if (req_all.loc[req_id, 'category'] == 'T'):
            theory_roomgroup[r_day, r_slot] = theory_roomgroup[r_day, r_slot]+1
        else:
            lab_roomgroup[r_day, r_slot] = lab_roomgroup[r_day, r_slot] + 1
    return timetable_np, theory_roomgroup, lab_roomgroup

def create_random_timetable(n_classes, n_days, n_slots, n_maxlecsperslot, req_all):
    timetable_np = np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan
    theory_roomgroup=np.zeros((n_days, n_slots))
    lab_roomgroup = np.zeros((n_days, n_slots))
    req_all['isAssigned']=False
    f_batch_can_overlap = da.initialize('batchcanoverlap').astype(int)
    batch_sets=get_groups_of_batches(f_batch_can_overlap)
    max_tries=n_days*n_slots

    for c in (set(req_all.classId)):  # First take one class
        req_class=req_all[(req_all['batchId'] != '-') & (req_all['classId'] == c)]
        for s in (set(req_class.subjectId)):
            req_subject=req_class[(req_class['subjectId'] == s)]
            for h in (set(req_subject.totalHrs)):
                req_hrs = req_subject[(req_subject['totalHrs'] == h)]
                for x in batch_sets:
                    req_batchset=set(req_hrs['batchId'].astype(int))
                    if(req_batchset<set(x)): #Then we can schedule that group of batches
                        req_set=req_hrs.index   #1. Get the requirements
                        r_day = random.randint(0, n_days - 1)   #2. Get the day and slot
                        r_slot = random.randint(0, n_slots - 1)
                        for i in req_set:  #Schedule each of these requirements
                            if (is_slot_available(req_all, timetable_np, c, r_day, r_slot, i, theory_roomgroup, lab_roomgroup)):
                                timetable_np, theory_roomgroup, lab_roomgroup = assign(timetable_np, int(c), r_day,
                                                                                           r_slot, i, req_all, theory_roomgroup, lab_roomgroup)
                                req_all.set_value(i, 'isAssigned', True)

    req_single = req_all[req_all['isAssigned']==False]
    for c in (set(req_single.classId)):  # First take one class
        req_forgivenclass = req_single.loc[req_single['classId'] == c]  # List all the requirements for that class in req_forgivenclass
        req_forgivenclass=req_forgivenclass.sort('eachSlot', ascending=False)
        req_set=req_forgivenclass.index
        for req in (req_set):  # Schedule each of these requirements
            notassigned = 1
            n_tries=0
            while (notassigned == 1 and n_tries<max_tries):  # Keep on scheduling till not found
                n_tries=n_tries+1
                r_day = random.randint(0,n_days-1)
                r_slot = random.randint(0,n_slots-1)
                if (is_slot_available(req_all, timetable_np, c, r_day, r_slot, req, theory_roomgroup, lab_roomgroup)):
                    timetable_np, theory_roomgroup, lab_roomgroup=assign(timetable_np, int(c), r_day, r_slot, req, req_all, theory_roomgroup, lab_roomgroup)
                    req_all.set_value(req, 'isAssigned', True)
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
req_single = pd.DataFrame(index=range(int(totallectures_list.sum())), columns=list(x))
j = 0
for i in range(len(req_single)):
    if((x.iloc[j]['totalHrs']/x.iloc[j]['eachSlot'])>0):
        req_single.loc[[i]] = x.iloc[[j]].values
        x.set_value(j,'totalHrs', x.loc[j]['totalHrs'] - x.loc[j]['eachSlot'])
    if (x.iloc[j]['totalHrs'] == 0):
        j = j + 1

req_single = req_single.rename(columns={'index': 'id'})
#print(req_all)
#These were attempts to convert float values in reqall to int
#req_all[['classId','eachSlot', 'subjectId', 'totalHrs']] = req_all[['classId','eachSlot', 'subjectId', 'totalHrs']].apply(pd.to_numeric)
#req_all=req_all.apply(pd.to_numeric, errors='ignore')

#These values need to be calculated from the database
#tt1=create_random_timetable(n_classes=14, n_days=5, n_slots=10, n_maxlecsperslot=4, req_all=req_all)
