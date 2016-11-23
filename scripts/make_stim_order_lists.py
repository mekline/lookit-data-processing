import random
import itertools

# useFallRotation
sets = []

for i in range(6):
	for j in range(i+1, 6):
		for k in range(j+1, 6):
			sets.append((i,j,k))

random.shuffle(sets)

for s in sets:
	print "[{}, {}, {}],".format(s[0], s[1], s[2])

# conceptOrderRotation

orders = list(itertools.permutations(['gravity', 'inertia', 'support', 'control']))
random.shuffle(orders)
for o in orders:
    print "['{}', '{}', '{}', '{}'],".format(o[0], o[1], o[2], o[3])

### gravityObjectRotation

print 'gravityObjectRotation'
# Gravity: First three comparisons are table (can't use spraybottle), next two are ramp (can't use orangeball)

orders = list(itertools.permutations(['apple', 'cup', 'lotion', 'orangeball', 'whiteball', 'spray']))
orders = [o for o in orders if 'spray' not in o[:3] and 'orangeball' not in o[3:5]]
random.shuffle(orders)
for o in orders:
    print "['{}', '{}', '{}', '{}', '{}', '{}'],".format(o[0], o[1], o[2], o[3], o[4], o[5])

### inertiaObjectRotation

print 'inertiaObjectRotation'
# Inertia: all objects are represented in stop and reverse
orders = list(itertools.permutations(['block', 'flashlight', 'marker', 'sunglasses', 'toycar', 'train']))
random.shuffle(orders)

# Remove effectively-equivalent orderings (since 1st 2 and 2nd 2 pairings are the same)
duplicates = []
for iO in range(len(orders)):
    newOrder = orders[iO]
    for jO in range(iO):
        oldOrder = orders[jO]
        if  newOrder[0] in oldOrder[:2] and \
            newOrder[1] in oldOrder[:2] and \
            newOrder[2] in oldOrder[2:4] and \
            newOrder[3] in oldOrder[2:4]:
            duplicates.append(iO)
orders = [orders[iO] for iO in range(len(orders)) if iO not in duplicates]

for o in orders:
    print "['{}', '{}', '{}', '{}', '{}', '{}'],".format(o[0], o[1], o[2], o[3], o[4], o[5])

### controlObjectRotation

print 'controlObjectRotation'
# Control: all objects are represented in same & salience
orders = list(itertools.permutations(['box', 'eraser', 'funnel', 'scissors', 'spoon', 'wrench']))

# Remove effectively-equivalent orderings (since 1st 3 and 2nd 3 pairings are the same)
duplicates = []
for iO in range(len(orders)):
    newOrder = orders[iO]
    for jO in range(iO):
        oldOrder = orders[jO]
        if  newOrder[0] in oldOrder[:3] and \
            newOrder[1] in oldOrder[:3] and \
            newOrder[2] in oldOrder[:3]:
            duplicates.append(iO)
orders = [orders[iO] for iO in range(len(orders)) if iO not in duplicates]

random.shuffle(orders)
for o in orders:
    print "['{}', '{}', '{}', '{}', '{}', '{}'],".format(o[0], o[1], o[2], o[3], o[4], o[5])

### supportObjectRotation

print 'supportObjectRotation'
# Support: all objects are represented in stay & fall
orders = list(itertools.permutations(['book', 'brush', 'duck', 'hammer', 'shoe', 'tissues']))

random.shuffle(orders)
for o in orders:
    print "['{}', '{}', '{}', '{}', '{}', '{}'],".format(o[0], o[1], o[2], o[3], o[4], o[5])
