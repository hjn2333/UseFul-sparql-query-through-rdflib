# @Time: 2023/3/26 10:25
# @Author: HJN
# @File: update_loc.py
# Software: PyCharm

from rdflib import Graph


def judge(x1, y1, x2, y2, radius):
    if (x2 - x1) ** 2 + (y2 - y1) ** 2 <= radius ** 2:
        return True
    else:
        return False


def parser_line(line):
    if line and len(line):
        items = line.split('#')
        if len(items) == 2:
            namespace = items[0]
            value = items[1]
            return namespace, value
    return 0


def addprefix(namespace, name):
    res = namespace + ':' + name
    return res


def updatelocation(g, namespace, rdfname, name, x, y):
    subject = addprefix(namespace, name)
    query1 = f""" 
    delete {{{subject} {namespace}:Location_x ?x}}
    insert {{{subject} {namespace}:Location_x "{x}"^^<http://www.w3.org/2001/XMLSchema#integer>}}
    where {{{subject} {namespace}:Location_x ?x}}
"""
    query2 = f"""
    delete {{{subject} {namespace}:Location_y ?y}}
    insert {{{subject} {namespace}:Location_y "{y}"^^<http://www.w3.org/2001/XMLSchema#integer>}}
    where {{{subject} {namespace}:Location_y ?y}}    
"""
    print(query1)
    print(query2)
    g.update(query1)
    g.update(query2)
    g.serialize(f"{rdfname}.ttl", format="turtle")
    print("RDF update success!")


def updateRelation(g, namespace, rdfname, relation_name, uav_name, station_name):
    subject = addprefix(namespace, uav_name)
    p = addprefix(namespace, relation_name)
    object = addprefix(namespace, station_name)
    query1 = f"""
    delete where {{{subject} {p} {object}}}
"""
    query2 = f"""
    insert data {{{subject} {p} {object}}}
"""
    g.update(query1)
    g.update(query2)
    g.serialize(f"{rdfname}", format="turtle")


def selectbytype(namespace, typename):
    g = Graph()
    query = f"""
    select ?subject where{{
    ?subject rdf:type <urn:absolute:{namespace}#{typename}>
    }}
"""
    res = []
    qres = g.query(query)
    for row in qres:
        for i in row:
            _, value = parser_line(i)
            res.append(value)
    return res


def deleteRelation(targetName, relationName, g):
    query = f"""
    delete{{:uav1 :{relationName} :{targetName}}}
    where{{:uav1 :{relationName} :{targetName}}}
"""
    g.update(query)
    g.serialize("uav.ttl", format="turtle")


def topologyIdentify(namespace, targetAgent):
    violate_list = []
    uav = addprefix(namespace, targetAgent)
    query = f"""select ?x, ?y where{{
        {uav} {namespace}:location_x ?x .
        {uav} {namespace}:location_y ?y 
    }}
    """
    g = Graph()
    g.parse(f"{namespace}.rdf")
    qres = g.query(query)
    uav_location = []
    for row in qres:
        for i in row:
            uav_location.append(i)
    query1 = f"""select ?x, ?y, ?radius, ?id, ?type where{{
        ?p rdf:type <obstruct> .
        ?p {namespace}:location_x ?x .
        ?p {namespace}:location_y ?y .
        ?p {namespace}:location_radius ?radius .
        ?p {namespace}:id ?id
        ?p {namespace}:type ?type
    }}"""
    qres1 = g.query(query1)
    for row in qres1:
        current_object = []
        for i in row:
            current_object.append(i)
        if judge(uav_location[0], uav_location[1], current_object[0], current_object[1], current_object[2]):
            violate_list.append(current_object)
    return violate_list, uav_location


def violate_handler(uav_location, violet_list):
    interferenceflag = False
    interferenceList = []
    stationflag = False
    newdirect_vector = 0
    type = 0
    if violet_list is None:
        return 0, newdirect_vector
    for i in violet_list:
        if i[4] == 1:  # station
            if interferenceflag is True:
                type = 1
                if interferenceList[0][1] == uav_location[1]:
                    newdirect_vector = 0
                elif interferenceList[0][0] == uav_location[0]:
                    type = 2
                    newdirect_vector = 0
                else:
                    direct_vector = (interferenceList[0][1] - uav_location[1]) / (interferenceList[0][0] - uav_location[0])
                    newdirect_vector = -direct_vector
        else:
            stationflag = True
        if i[4] == 2:  # interference
            if stationflag is True:
                type = 1
                if i[1] == uav_location[1]:
                    newdirect_vector = 0
                elif i[0] == uav_location[0]:
                    return 2, 0  # 代表斜率为正无穷
                else:
                    direct_vector = (i[1] - uav_location[1]) / (i[0] - uav_location[0])
                    newdirect_vector = -1 / direct_vector
                return type, newdirect_vector
            else:
                interferenceflag = True
                interferenceList.append([i[1], i[2]])
        if i[4] == 3:  # obstruct should be avoided immediately
            if i[1] == uav_location[1]:
                newdirect_vector = 0
            elif i[0] == uav_location[0]:
                return 2, 0  # 代表斜率为正无穷
            else:
                direct_vector = (i[1]-uav_location[1])/(i[0]-uav_location[0])
                newdirect_vector = -1/direct_vector
            return type, newdirect_vector
        else:
            print("Wrong status!")
    if stationflag is True:  # only when uav inside station and interference will change its route
        return type, newdirect_vector
    else:
        return type, newdirect_vector
