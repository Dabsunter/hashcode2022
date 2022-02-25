#!/usr/bin/env python3

import os
import sys
from tqdm import trange,tqdm
import threading
from scipy.optimize import differential_evolution

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

skills = {}

def get_skilled_persons(skill):
    global skills
    if skill not in skills:
        skills[skill] = []
    return skills[skill]

class Person:
    def __init__(self):
        self.name, nb_skills = input().split()
        nb_skills = int(nb_skills)
        self.skills = {}
        for _ in range(nb_skills):
            skill,level = input().split()
            lvl = int(level)
            self.skills[skill] = lvl
            get_skilled_persons(skill).append((self.name, lvl))
        
        self.taken_until = 0

    def get_level(self, skill):
        if skill in self.skills:
            return self.skills[skill]
        return 0

    def get_nb_skills(self):
        return len(self.skills)


class Project:
    def __init__(self):
        self.name,d,s,b,r = input().split()
        self.duration = int(d)
        self.reward = int(s)
        self.deadline = int(b)
        nb_role = int(r)
        self.needed_skills = []
        for _ in range(nb_role):
            skill,level = input().split()
            self.needed_skills.append((skill,int(level)))

nb_person,nb_project = input().split()
nb_person = int(nb_person)
nb_project = int(nb_project)

eprint("\n## Read persons")

persons = [Person() for _ in trange(nb_person)]

eprint("\n## Read projects")

projects = [Project() for _ in trange(nb_project)]


# Sort ascending skills
eprint("\n# Sort skills")
for skill,skilled in skills.items():
    skilled.sort(key=lambda p: p[1], reverse=True)
    # eprint(skill, ":", end='\t')
    # for p in skilled: eprint(p[0] + " (" + str(p[1]) + ") ", end=' ')
    # eprint()

#eprint("skills", skills)


# Remove impossible projects
eprint("\n# Remove impossible projects")
# for p in projects:
#     rm = False
#     for sk,lvl in p.needed_skills:
#         eprint(p.name,sk,"lvl", lvl)
#         rm |= get_skilled_persons(sk)[0][1] < lvl
#     if rm:
#         projects.remove(p)
#         # eprint("projet impossible:", p.name)

def can_do_it(proj):
    for sk,lvl, in proj.needed_skills:
        if get_skilled_persons(sk)[0][1] < lvl:
            return False
    return True

projects = [p for p in projects if can_do_it(p)]

eprint("projets possibles:", [p.name for p in projects])

# Planning

def project_priority(p: Project):
    return p.deadline

projects.sort(key=project_priority)
ordered_projects = projects

needed_skills = [sk for p in ordered_projects for sk in p.needed_skills]

# Borne sup
def bound_for_skill(skill, level):
    skilled = get_skilled_persons(skill)
    i = 1
    while i < len(skilled) and skilled[i][1] >= level:
        i+=1
    return i



# la fitness
def compute_score(x):
    x = [int(i) for i in x]
    projects = ordered_projects.copy()
    aviability = {p.name: 0 for p in persons}
    day = 0
    score = 0

    cancelled_projects = set()
    teams = {}
    i = 0
    for proj in projects:
        t = []
        teams[proj.name] = t
        for skill,_ in proj.needed_skills:
            skilled = get_skilled_persons(skill)
            new_member = skilled[x[i]][0]

            if new_member in t:
                cancelled_projects.add(proj.name)

            t.append(new_member)
            i+=1

    projects = [p for p in projects if p.name not in cancelled_projects]

    def is_ready(proj):
        for pers in teams[proj.name]:
            if aviability[pers] > day:
                return False
        return True

    def pick_project():
        for k,proj in enumerate(projects):
            if is_ready(proj):
                return projects.pop(k)

    while len(projects) > 0:
        proj = pick_project()

        while proj != None:
            for pers in teams[proj.name]:
                aviability[pers] = day + proj.duration

            score += max(0, proj.reward - max(0, day + proj.duration + 1 - proj.deadline))

            proj = pick_project()

        day += 1



    return -score # differential_evolution cherche le min

eprint("\n# Let darwin do its job")

bounds = [(0, bound_for_skill(*sk)) for sk in needed_skills]

# eprint("bounds:", bounds, sep='\n')

cout = sys.stdout
sys.stdout = sys.stderr

res = differential_evolution(
    compute_score,
    bounds=bounds,
    disp=True,
    workers=12,
    updating='deferred',
    popsize=int(os.getenv('POPSIZE',12)),
    maxiter=int(os.getenv('MAXITER', 1000)),
    recombination=float(os.getenv('CROSSOVER', 0.2)),
    mutation=float(os.getenv('MUTATION', 0.7))
)

sys.stdout = cout

# eprint(res.x)

eprint("\n# Printing results")

# eprint("expected score:", -compute_score(res.x))

# sys.exit(0)

# eprint("x len:", len(res.x))
# eprint("sum of needed skills:", sum([len(p.needed_skills) for p in ordered_projects]))

# eprint("\n# check bounds")

# for i,(x,(m,M)) in enumerate(zip(res.x,bounds)):
#     if x<m or x>=M:
#         eprint("invalid bounds:", i,x,m,M)

# eprint(*[str(i) + "\t" + str(a) + "\t" + str(b) + '\t' + str(c) for i,(a,b,c) in enumerate(zip(bounds, [(0, bound_for_skill(*sk)) for sk in needed_skills], needed_skills))], sep='\n')
                

# Print results
# result = []
# i = 0
# for proj in ordered_projects:
#     valid = True
#     t = []
#     for skill,_ in proj.needed_skills:
#         # crado mais tanpis
#         skilled = get_skilled_persons(skill)
#         x = int(res.x[i])
#         eprint(i, res.x[i], x, bounds[i], bound_for_skill(skill,_), len(skilled), sep='\t')
#         new_member = skilled[x][0]

#         j = 1
#         while j <= len(skilled) and new_member in t:
#             new_member = skilled[x-j][0]
#             j+=1

#         valid = not new_member in t
#         if not valid:
#             break

#         t.append(new_member)
#         i+=1

#     if valid:
#         result.append((proj.name,t))


x = [int(i) for i in res.x]
result = []
i = 0
for proj in ordered_projects:
    valid = True
    t = []
    for skill,_ in proj.needed_skills:
        skilled = get_skilled_persons(skill)
        new_member = skilled[x[i]][0]
        i+=1
        valid &= not new_member in t
        if valid:
        # try:
            t.append(new_member)
        # except IndexError:
        #     eprint(i, x[i], bounds[i], bound_for_skill(skill,_), len(skilled), needed_skills[i], sep='\t')
        #     sys.exit(1)

    if valid:
        result.append((proj.name, t))



print(len(result))
for p,t in result:
    print(p)
    print(*t)