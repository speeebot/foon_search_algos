import pickle
import json
from collections import OrderedDict
from FOON_class import Object

# -----------------------------------------------------------------------------------------------------------------------------#
# Checks an ingredient exists in kitchen
def check_if_exist_in_kitchen(kitchen_items, ingredient):
    """
        parameters: a list of all kitchen items,
                    an ingredient to be searched in the kitchen
        returns: True if ingredient exists in the kitchen
    """

    for item in kitchen_items:
        if item["label"] == ingredient.label \
                and sorted(item["states"]) == sorted(ingredient.states) \
                and sorted(item["ingredients"]) == sorted(ingredient.ingredients) \
                and item["container"] == ingredient.container:
            return True

    return False
# -----------------------------------------------------------------------------------------------------------------------------#

def search_BFS(kitchen_items=[], goal_node=None):
    # list of indices of functional units
    reference_task_tree = []

    # list of object indices that need to be searched
    items_to_search = []

    # find the index of the goal node in object node list
    items_to_search.append(goal_node.id)

    # list of item already explored
    items_already_searched = []

    while len(items_to_search) > 0:
        current_item_index = items_to_search.pop(0)  # pop the first element
        if current_item_index in items_already_searched:
            continue
        else:
            items_already_searched.append(current_item_index)

        current_item = foon_object_nodes[current_item_index]

        if not check_if_exist_in_kitchen(kitchen_items, current_item):

            candidate_units = foon_object_to_FU_map[current_item_index]

            # selecting the first path
            # this is the part where you should use heuristic for Greedy Best-First search
            selected_candidate_idx = candidate_units[0]

            # if a functional unit is already taken, do not process it again
            if selected_candidate_idx in reference_task_tree:
                continue

            reference_task_tree.append(selected_candidate_idx)

            # all input of the selected functional unit need to be explored
            for node in foon_functional_units[selected_candidate_idx].input_nodes:
                node_idx = node.id
                if node_idx not in items_to_search:
                # if in the input nodes, we have bowl contains {onion} and onion, chopped, in [bowl]
                # explore only onion, chopped, in bowl
                    flag = True
                    if node.label in utensils and len(node.ingredients) == 1:
                        #print(f"object: {node.label}")
                        #print(f"contains: {node.ingredients}")
                        for node2 in foon_functional_units[selected_candidate_idx].input_nodes:
                            if node2.label == node.ingredients[0] and node2.container == node.label:
                                flag = False
                                break
                    if flag:
                        items_to_search.append(node_idx)

    # reverse the task tree
    reference_task_tree.reverse()

    # create a list of functional units from the indices of reference_task_tree
    task_tree_units = []
    for i in reference_task_tree:
        task_tree_units.append(foon_functional_units[i])

    return task_tree_units

def search_IDS(kitchen_items=[], goal_node=None):
    # list of indices of functional units
    reference_task_tree = []
    depth = 0
    max_depth = 50
    remaining = True
    
    # call depth first search starting from the goal node
    while depth < max_depth:
        remaining = DFS(depth, max_depth, goal_node.id, reference_task_tree, kitchen_items)
        depth += 1

    # reverse the task tree
    reference_task_tree.reverse()

    # create a list of functional units from the indices of reference_task_tree
    task_tree_units = []
    for i in reference_task_tree:
        task_tree_units.append(foon_functional_units[i])

    return task_tree_units 

def DFS(depth, max_depth, current_item_index, reference_task_tree, kitchen_items=[]):
    # grab nodes of current foon object
    current_item = foon_object_nodes[current_item_index] 

    # for each node, check if the ingredient already exists in the kitchen
    if check_if_exist_in_kitchen(kitchen_items, current_item):
        pass
    else: 
        #candidate_units are all of the functional units which contain the output node we are looking to create
        candidate_units = foon_object_to_FU_map[current_item_index]

        # select the first path
        selected_candidate_idx = candidate_units[0]
        
        if depth < 0: #reaches bound
            for node in foon_functional_units[selected_candidate_idx].input_nodes:
                if not check_if_exist_in_kitchen(kitchen_items, foon_object_nodes[node.id]):
                    if selected_candidate_idx not in reference_task_tree:
                        return True
            return False

        if depth > 0:
            # explore all input nodes of the selected functional unit
            for node in foon_functional_units[selected_candidate_idx].input_nodes:
                node_index = node.id
                flag = True
                if node.label in utensils and len(node.ingredients) == 1:
                    for node2 in foon_functional_units[selected_candidate_idx].input_nodes:
                        if node2.label == node.ingredients[0] and node2.container == node.label:
                            flag = False
                            break
                if flag:
                    status = DFS(depth-1, max_depth, node_index, reference_task_tree, kitchen_items)
                    if selected_candidate_idx in reference_task_tree:
                        pass
                    else:
                        reference_task_tree.append(selected_candidate_idx)

    return False

#In case of heuristic 1, if you have multiple path with different motions, choose the
#path that gives higher success rate of executing the motion successfully. For
#example, a robot has higher success rate of pouring sliced onion compared to
#slicing a whole onion. The success rate of each motion is provided in the
#motion.txt file
def find_best_success_rate_candidate(candidate_units):
    motion_file = open('motion.txt', 'r')
    with open('motion.txt', 'r') as f:
        lines = f.readlines()

    motions = {}

    for line in lines:
        motion_name = line.split('\t')[0]
        motion_rate = line.split('\t')[1]
        motions[motion_name] = motion_rate

    candidate_motions = {}
    
    for unit in candidate_units:
        candidate_motion = foon_functional_units[unit].motion_node
        candidate_motions[candidate_motion] = motions[candidate_motion]

    best_candidate = max(candidate_motions, key=candidate_motions.get)
        
    for unit in candidate_units:
        if foon_functional_units[unit].motion_node == best_candidate:
            best_unit = unit

    return best_unit

def search_heuristic1(kitchen_items=[], goal_node=None):
    # list of indices of functional units
    reference_task_tree = []

    # list of object indices that need to be searched
    items_to_search = []

    # find the index of the goal node in object node list
    items_to_search.append(goal_node.id)

    # list of item already explored
    items_already_searched = []

    while len(items_to_search) > 0:
        current_item_index = items_to_search.pop(0)  # pop the first element

        if current_item_index in items_already_searched:
            continue
        else:
            items_already_searched.append(current_item_index)

        current_item = foon_object_nodes[current_item_index] 

        if not check_if_exist_in_kitchen(kitchen_items, current_item): #if goal node doesnt exist, we find steps to make it, otherwise nothing to do

            candidate_units = foon_object_to_FU_map[current_item_index]

            # selecting the first path
            # this is the part where you should use heuristic for Greedy Best-First search
            selected_candidate_idx = find_best_success_rate_candidate(candidate_units)
            #selected_candidate_idx = candidate_units[0]
            # If we find that there are more than one way to get the egg mixture, you can choose the first way you
            # discover in case of iterative deepening. But, when you are using heuristic, you need to check all the 
            # candidate functional units and calculate the cost of the heuristic function. Then, you can decide which path to choose
            
            # if a functional unit is already taken, do not process it again
            if selected_candidate_idx in reference_task_tree:
                continue

            reference_task_tree.append(selected_candidate_idx)

            # all input of the selected functional unit need to be explored
            for node in foon_functional_units[selected_candidate_idx].input_nodes:
                node_idx = node.id
                if node_idx not in items_to_search:
                    # if in the input nodes, we have bowl contains {onion} and onion, chopped, in [bowl]
                    # explore only onion, chopped, in bowl
                    flag = True
                    if node.label in utensils and len(node.ingredients) == 1:
                        for node2 in foon_functional_units[selected_candidate_idx].input_nodes:
                            if node2.label == node.ingredients[0] and node2.container == node.label:
                                flag = False
                                break
                    if flag:
                        items_to_search.append(node_idx)

    # reverse the task tree
    reference_task_tree.reverse()

    # create a list of functional unit from the indices of reference_task_tree
    task_tree_units = []
    for i in reference_task_tree:
        task_tree_units.append(foon_functional_units[i])

    return task_tree_units 

#count input objects of candidate unit, including object ingredients
def count_input_objects(candidate_unit):
    count = 0
    input_objects = []

    for node in foon_functional_units[candidate_unit].input_nodes:
        for ingredient in node.ingredients:
            count += 1
            input_objects.append(ingredient)
        if node.label not in input_objects:
            count += 1
            input_objects.append(node.label)

    return count

#returns functional_unit index for functional unit that contains the least input objects
#input objects includes object ingredients
def find_least_input_objects_candidate(candidate_units):
    candidate_input_dict = {}

    for unit in candidate_units:
        candidate_input_dict[unit] = count_input_objects(unit)

    best_candidate = min(candidate_input_dict, key=candidate_input_dict.get)

    return best_candidate

def search_heuristic2(kitchen_items=[], goal_node=None):
    # list of indices of functional units
    reference_task_tree = []

    # list of object indices that need to be searched
    items_to_search = []

    # find the index of the goal node in object node list
    items_to_search.append(goal_node.id)

    # list of item already explored
    items_already_searched = []

    while len(items_to_search) > 0:
        current_item_index = items_to_search.pop(0)  # pop the first element

        if current_item_index in items_already_searched:
            continue
        else:
            items_already_searched.append(current_item_index)

        current_item = foon_object_nodes[current_item_index] 

        if not check_if_exist_in_kitchen(kitchen_items, current_item):

            candidate_units = foon_object_to_FU_map[current_item_index]

            # selecting the first path
            # this is the part where you should use heuristic for Greedy Best-First search
            #selected_candidate_idx = candidate_units[0]
            selected_candidate_idx = find_least_input_objects_candidate(candidate_units)
            # If we find that there are more than one way to get the egg mixture, you can choose the first way you
            # discover in case of iterative deepening. But, when you are using heuristic, you need to check all the 
            # candidate functional units and calculate the cost of the heuristic function. Then, you can decide which path to choose
            
            # if a functional unit is already taken, do not process it again
            if selected_candidate_idx in reference_task_tree:
                continue

            reference_task_tree.append(selected_candidate_idx)

            # all input of the selected functional unit need to be explored
            for node in foon_functional_units[selected_candidate_idx].input_nodes:
                node_idx = node.id
                if node_idx not in items_to_search:
                    # if in the input nodes, we have bowl contains {onion} and onion, chopped, in [bowl]
                    # explore only onion, chopped, in bowl
                    flag = True
                    if node.label in utensils and len(node.ingredients) == 1:
                        for node2 in foon_functional_units[selected_candidate_idx].input_nodes:
                            if node2.label == node.ingredients[0] and node2.container == node.label:
                                flag = False
                                break
                    if flag:
                        items_to_search.append(node_idx)

    # reverse the task tree
    reference_task_tree.reverse()

    # create a list of functional unit from the indices of reference_task_tree
    task_tree_units = []
    for i in reference_task_tree:
        task_tree_units.append(foon_functional_units[i])

    return task_tree_units 

def save_paths_to_file(task_tree, path):

    print('writing generated task tree to ', path)
    _file = open(path, 'w')

    _file.write('//\n')
    for FU in task_tree:
        _file.write(FU.get_FU_as_text() + "\n")
    _file.close()

# -----------------------------------------------------------------------------------------------------------------------------#
# creates the graph using adjacency list
# each object has a list of functional list where it is an output
def read_universal_foon(filepath='FOON.pkl'):
    """
        parameters: path of universal foon (pickle file)
        returns: a map. key = object, value = list of functional units
    """
    pickle_data = pickle.load(open(filepath, 'rb'))
    functional_units = pickle_data["functional_units"]
    object_nodes = pickle_data["object_nodes"]
    object_to_FU_map = pickle_data["object_to_FU_map"]

    return functional_units, object_nodes, object_to_FU_map
# -----------------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    foon_functional_units, foon_object_nodes, foon_object_to_FU_map = read_universal_foon()

    utensils = []
    with open('utensils.txt', 'r') as f:
        for line in f:
            utensils.append(line.rstrip())

    kitchen_items = json.load(open('kitchen.json'))

    goal_nodes = json.load(open("goal_nodes.json"))

    for node in goal_nodes:
        node_object = Object(node["label"])
        node_object.states = node["states"]
        node_object.ingredients = node["ingredients"]
        node_object.container = node["container"]

        for object in foon_object_nodes:
            if object.check_object_equal(node_object):
                output_task_tree = search_BFS(kitchen_items, object)
                save_paths_to_file(output_task_tree,
                                   'output_BFS_{}.txt'.format(node["label"]))
                output_task_tree = search_heuristic1(kitchen_items, object)
                save_paths_to_file(output_task_tree,
                                   'output_heuristic1_{}.txt'.format(node["label"]))
                output_task_tree = search_heuristic2(kitchen_items, object)
                save_paths_to_file(output_task_tree,
                                   'output_heuristic2_{}.txt'.format(node["label"]))
                output_task_tree = search_IDS(kitchen_items, object)
                save_paths_to_file(output_task_tree,
                                   'output_IDS_{}.txt'.format(node["label"]))
                break