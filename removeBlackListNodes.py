import csv


def remove_blacklist():
    node_file = csv.reader(open("nyc_map4/nodes.csv", 'rb'))
    list_of_nodes = []
    for row in node_file:
        list_of_nodes.append(row)
    final_list_of_nodes = []
    black_list = csv.reader(open("nyc_map4/Blacklist.csv", 'r'))
    set_of_blacklist = set()
    for row in black_list:
        set_of_blacklist.add(row[2])
    i = 0
    for Node in list_of_nodes:
        if i == 0 or Node[0] not in set_of_blacklist:
            final_list_of_nodes.append(Node)
        i += 1
    node_file = csv.writer(open("nyc_map4/nodes.csv", 'wb'))
    for row in final_list_of_nodes:
        node_file.writerow(row)

if __name__ == '__main__':
    remove_blacklist()
