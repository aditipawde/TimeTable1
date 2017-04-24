import dataAccessSQLAlchemy as da
import pandas as pd
import random
import numpy as np


def create_random_timetable(n_classes, n_days, n_slots, n_maxlecsperslot, req_all):

    timetable_np = np.empty((n_classes, n_days, n_slots, n_maxlecsperslot)) * np.nan
    theory_roomgroup = np.zeros((n_days, n_slots))
    lab_roomgroup = np.zeros((n_days, n_slots))

    # print(timetable_np)
    f_batch_can_overlap = da.initialize('batchcanoverlap').astype(int)
    batch_sets = get_groups_of_batches(f_batch_can_overlap) 

    max_tries = n_days * n_slots

    flatten = lambda batch_sets: [item for sublist in batch_sets for item in sublist]

    batch_sets_f = flatten(batch_sets)

    req_batch = req_all[req_all['batchId'].isin(batch_sets_f)]
    req_single = req_all[~req_all['batchId'].isin(batch_sets_f)]

    # Batch assignment
    for c in (set(req_batch.classId)):  # First take one class

        req_forgivenclass = req_batch.loc[req_batch['classId'] == c]  # List all the requirements for that class in req_forgivenclass
        req_forgivenclass = req_forgivenclass.sort('eachSlot', ascending=False)
        req_set = req_forgivenclass.index

        for i in range(len(batch_sets)):

            if(set(batch_sets[i]) < set(req_set)):   #Check if the batch set is a subset of the req set. If yes, Now we have to scedule this bunch of requirements.

                notassigned = len(batch_sets[i])
                n_tries = 0

                while (notassigned > 0 and n_tries < max_tries):  # Keep on scheduling till not found

                    n_tries = n_tries + 1
                    r_day = random.randint(0, n_days - 1)
                    r_slot = random.randint(0, n_slots - 1)

                    for j in range(len(batch_sets[i])):

                        req = batch_sets[i][j]

                        if (is_slot_available(req_batch, timetable_np, c, r_day, r_slot, req, theory_roomgroup, lab_roomgroup)):

                            timetable_np = assign(timetable_np, int(c), r_day, r_slot, req)
                            notassigned = notassigned - 1

                    if (notassigned > 0 and n_tries < max_tries):

                        #Then Undo all the assignments
                        for j in range(len(batch_sets[i])):

                            req = batch_sets[i][j]

                            if req in timetable_np:

                                timetable_np[timetable_np == req] = np.nan
                                notassigned = notassigned + 1

    # Theory assignment
    for c in (set(req_single.classId)):  # First take one class

        req_forgivenclass = req_single.loc[req_single['classId'] == c]  # List all the requirements for that class in req_forgivenclass
        req_forgivenclass = req_forgivenclass.sort('eachSlot', ascending=False)
        req_set = req_forgivenclass.index

        for i in range(len(req_set)):  # Schedule each of these requirements

            req = req_set[i]
            notassigned = 1

            while (notassigned == 1):  # Keep on scheduling till not found

                r_day = random.randint(0,n_days-1)
                r_slot = random.randint(0,n_slots-1)

                if (is_slot_available(req_single, timetable_np, c, r_day, r_slot, req, theory_roomgroup, lab_roomgroup)):

                    timetable_np=assign(timetable_np, int(c), r_day, r_slot, req)
                    notassigned = 0


    return timetable_np
