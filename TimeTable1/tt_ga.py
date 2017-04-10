import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np
import main_ravina as t
import costFunctions as cost

def initialize_population(p):
    P=[None]*p
    print("initialising population...")
    for i in range(p):
        tt = t.create_random_timetable(n_classes=14, n_days=5, n_slots=10, n_maxlecsperslot=5, req_all=t.req_all)
        P[i]=tt
        print(i)
    return P

def find_objective(h):
    penalty=cost.get_cost(h,t.req_all, 4, 4)
    return penalty

def crossover(tt1, tt2):
    n_classes, n_days, n_slots, n_maxlecsperslot = tt1.shape
    new_h1= np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan
    new_h2 = np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan
    #Change remove 4
    for c in range(n_classes):
        req_for_c = t.req_all.loc[t.req_all['classId'] == c]
        req_h1=[]
        req_h2=[]
        for d in range(n_days):
            for s in range(n_slots):
                #can drill down to subslot level if required
                selected_tt=random.randint(0,1)
                if(selected_tt==0):
                    for req_id in tt1[c, d, s, :]:
                        if(np.isnan(req_id)): continue
                        if(req_h1 is not None and not req_id in req_h1):
                            if(t.is_slot_available(t.req_all, new_h1, c, d, s, req_id)):
                                new_h1=t.assign(new_h1, c, d, s, req_id)
                                req_h1.append(req_id)

                    for req_id in tt2[c, d, s, :]:
                        if (np.isnan(req_id)): continue
                        if (req_h2 is not None and not req_id in req_h2):
                            if (t.is_slot_available(t.req_all, new_h2, c, d, s, req_id)):
                                new_h2 = t.assign(new_h2, c, d, s, req_id)
                                req_h2.append(req_id)

                else:
                    for req_id in tt2[c, d, s, :]:
                        if(np.isnan(req_id)): continue
                        if(req_h1 is not None and not req_id in req_h1):
                            if(t.is_slot_available(t.req_all, new_h1, c, d, s, req_id)):
                                new_h1=t.assign(new_h1, c, d, s, req_id)
                                req_h1.append(req_id)
                    for req_id in tt1[c, d, s, :]:
                        if(np.isnan(req_id)): continue
                        if(req_h2 is not None and not req_id in req_h2):
                            if (t.is_slot_available(t.req_all, new_h2, c, d, s, req_id)):
                                new_h2 = t.assign(new_h2, c, d, s, req_id)
                                req_h2.append(req_id)

        #Now, after all the requirements of class c have been crossovered, we check for any missing requirements and fill it
        #First for h1

        req_for_c = t.req_all.loc[t.req_all['classId'] == c]
        #s = np.unique(timetable[c])
        #missing = [x for x in req_for_c.index if x not in s]
        #s_h1 = set(req_h1)
        s_h1=set(np.unique(new_h1[c]))
        s_req_for_c=set(req_for_c.index)
        missing_h1 = list(s_req_for_c-s_h1)
        if(len(missing_h1)>0):
            for d in range(n_days):
                for s in range(n_slots):
                    if(t.is_slot_available(t.req_all, new_h1, c, d, s, missing_h1[0])):
                        new_h1 = t.assign(new_h1, c, d, s, missing_h1[0])
                        req_h1.append(missing_h1[0])
                        missing_h1.pop(0)
                        if (len(missing_h1) == 0):
                            break
                    if (len(missing_h1) == 0):
                        break
                if (len(missing_h1) == 0):
                    break
        #Now for h2

        s_h2 = set(np.unique(new_h2[c]))
        missing_h2 = list(s_req_for_c - s_h2)
        if(len(missing_h2)>0):
            for d in range(n_days):
                for s in range(n_slots):
                    if(t.is_slot_available(t.req_all, new_h2, c, d, s, missing_h2[0])):
                        new_h2 = t.assign(new_h2, c, d, s, missing_h2[0])
                        req_h2.append(missing_h2[0])
                        missing_h2.pop(0)
                        if (len(missing_h2) == 0):
                            break
                    if (len(missing_h2) == 0):
                        break
                if (len(missing_h2) == 0):
                    break

    return new_h1, new_h2


def mutate(tt):
    n_classes, n_days, n_slots, n_maxlecsperslot = tt.shape
    #take some random requirement
    req_id=random.randint(0,len(t.req_all)-1)
    #Here, in order to mutate I just pick up 1 requirement, and schedule it in an empty slot.
    #Step 1. Delete the requirement from the tt
    tt[tt == req_id] = np.nan
    c=t.req_all.loc[req_id, 'classId']
    assigned=0
    for d in range(n_days):
        for s in range(n_slots):
            if (t.is_slot_available(t.req_all, tt, c, d, s, req_id)):
                tt = t.assign(tt, c, d, s, req_id)
                assigned=1
                break
        if(assigned==1): break
    return tt


def run_genetic(objective_threshold, p, r, m, max_iterations):
    P=initialize_population(p)
    Objective_P=np.empty(p)
    i=0
    for h in P:
        Objective_P[i]=find_objective(h)
        i = i + 1
    print(Objective_P)
    n_iterations=0
    while(np.min(Objective_P)>=objective_threshold and n_iterations<max_iterations):
        P_s=[None]*p
        #SELECT PHASE
        retained_population=int((1-r)*p)
        weighted_list=[]
        for j in range(p):
            weighted_list=weighted_list+([j] * int(np.sum(Objective_P)-(Objective_P[j])))   #Need to give higher weightage for lower objective function
        for j in range(retained_population):
            weighted_random_tt=random.choice(weighted_list)
            P_s[j]=P[weighted_random_tt]

        #CROSSOVER PHASE
        for j in range(retained_population, p, 2):
            h1=random.choice(weighted_list)
            h2=random.choice(weighted_list)
            new_h1, new_h2=crossover(P[h1], P[h2])
            if(j+1==p): P_s[j]=new_h1
            else: P_s[j], P_s[j+1]=new_h1, new_h2

        #MUTATE PHASE
        for j in range(int(r*p)):    #Mutate rp of all TTs
            tt_mutate=random.randint(0,p-1)
            P_s[tt_mutate]=mutate(P_s[tt_mutate])

        #UPDATE PHASE
        P=P_s

        #EVALUATE PHASE
        i = 0
        for h in P:
            Objective_P[i] = find_objective(h)
            i = i + 1
        print(Objective_P)

        print("Completed iteration ", n_iterations)
        n_iterations=n_iterations+1

    best_tt=np.argmin(Objective_P)
    print("selected TT ", best_tt)

    return P[best_tt]


finalTT=run_genetic(objective_threshold=0, p=300, r=0.7, m=0.01, max_iterations=300) #p=population size, r=crossover fraction, m=mutation rate


print(finalTT)

n_classes, n_days, n_slots, n_maxlecsperslot = finalTT.shape
for c in range(n_classes):
    for d in range(n_days):
        np.savetxt('finalTT_'+str(c)+"_"+str(d)+'.csv', finalTT[c][d], delimiter=',')

print("Yayyy DOne!")