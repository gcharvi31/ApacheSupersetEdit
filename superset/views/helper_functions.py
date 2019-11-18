import os
import json
import copy
import argparse

# parser = argparse.ArgumentParser(description='Script to change datasource for dashboard')
# parser.add_argument("--old_dshbd", default = None, type=str, help = "Old dashboard json object")
# parser.add_argument("--new_dshbd_name", default = "dash_new", type=str, help = "Name of new dashboard")
# parser.add_argument("--database_id_list", default = None, type=list, help = "List of database id's from which slices have to be made")
# parser.add_argument("--database_name_list", default = None, type=list, help = "List of database names from which slices have to be made")
# parser.add_argument("--datasource_id_list", default = None, type=list, help = "List of datasource id's from which slices have to be made")
# parser.add_argument("--datasource_name_list", default = None, type=list, help = "List of datasource names from which slices have to be made")
# parser.add_argument("--slice_name_list", default = None, type=list, help = "List of new slice names")

# args = parser.parse_args()

def modify_dashboard_name(old_dshbd, new_dshbd_name, new_dshbd_id = 0):
    """ Function to make a new dashboard with new name and id.
    Default new_dshbd_id = 0. Apache Superset automatically assigns next dashboard number.
    """
    
    dshbd = copy.deepcopy(old_dshbd)
    
    # Get __Dashboard__ dict from dashboards dict in json metadata
    dshbd_subdict = dshbd["dashboards"][0]["__Dashboard__"]
        
    # Modify old dashboard
    dshbd_subdict["dashboard_title"] = new_dshbd_name 
    # dshbd_subdict["id"] = new_dshbd_id

    json_metadata = json.loads(dshbd_subdict["json_metadata"])
    # json_metadata["remote_id"] = new_dshbd_id
    dshbd_subdict["json_metadata"] = json.dumps(json_metadata)
    
    position_json = json.loads(dshbd_subdict["position_json"])
    position_json["HEADER_ID"]["meta"]["text"] = new_dshbd_name
    dshbd_subdict["position_json"] = json.dumps(position_json)
       
    return dshbd

def modify_slice_info(chart, database_name, datasource_name, datasource_id, slice_name):
    """Modify each slice info and return new slice
    """ 
    chart["datasource_name"] = datasource_name
    # chart["datasource_id"] = datasource_id
    chart["slice_name"] = slice_name
    # chart["perm"] = "[" + database_name + "]" + "." + "[" + datasource_name + "]" + "(" + "id:" + str(datasource_id) + ")"

    params = json.loads(chart["params"])
    params["datasource"] = str(datasource_id) + "__table"
    params["datasource_name"] = datasource_name
    # params["schema"] = datasource_name
    params["database_name"] = database_name
    chart["params"] = json.dumps(params)
    
    return chart

def modify_slices_info(dshbd, database_name_list, datasource_name_list, datasource_id_list, slice_name_list):
    """Extract slice-table_name info of all slices present in the dashboard
    """

    all_slices = dshbd["dashboards"][0]["__Dashboard__"]["slices"]
    num_slices = len(all_slices)
    for i in range(len(all_slices)):
        chart = all_slices[i]["__Slice__"]
        chart = modify_slice_info(chart, database_name_list[i], datasource_name_list[i], 
                                  datasource_id_list[i], slice_name_list[i])

    position_json = json.loads(dshbd["dashboards"][0]["__Dashboard__"]["position_json"])
    slice_list = [value for key, value in position_json.items() if "CHART" in key]
    for i in range(len(slice_list)):
        slice_list[i]["meta"]["sliceName"] = slice_name_list[i]        
    dshbd["dashboards"][0]["__Dashboard__"]["position_json"] = json.dumps(position_json)
      
    return dshbd

def modify_datasources_info(dshbd, database_id_list, database_name_list, datasource_name_list, datasource_id_list, slice_name_list):
    datasources = dshbd["datasources"]
    for i in range(len(datasources)):
        d = datasources[i]["__SqlaTable__"]
        d["table_name"] = datasource_name_list[i]
        # d["id"] = datasource_id_list[i]
        # d["perm"] = "[" + database_name_list[i] + "]" + "." + "[" + datasource_name_list[i] + "]" + "(" + "id:" + str(datasource_id_list[i]) + ")"
        d["database_id"] = database_id_list[i]        
        
        params = json.loads(d["params"])
        params["remote_id"] = datasource_id_list[i]
        params["database_name"] = database_name_list[i]
        d["params"] = json.dumps(params)
        
        # d["database"]["__Database__"]["id"] = database_id_list[i]
        # d["database"]["__Database__"]["perm"] = "[" + database_name_list[i] + "]" + "." + "(" + "id:" + str(database_id_list[i]) + ")"
        
        table_id = datasource_id_list[i]
        for j in range(len(d["columns"])):
             d["columns"][j]["__TableColumn__"]["table_id"] = table_id        
            
        for j in range(len(d["metrics"])):
            d["metrics"][j]["__SqlMetric__"]["table_id"] = table_id  
    
    dshbd["datasources"] = datasources
    
    return dshbd

def current_slices_info(dshbd):
    """Extract current dashboard slice info return into json object"""

    all_slices = dshbd["dashboards"][0]["__Dashboard__"]["slices"]
    num_slices = len(all_slices)
    l1, l2, l3 = [], [], []
    for i in range(len(all_slices)):
        chart = all_slices[i]["__Slice__"]
        l1.append(chart['slice_name'])
        l2.append(json.loads(chart['params'])['datasource_name'])
        l3.append(json.loads(chart['params'])['database_name'])
     
    sliceinfo = {'slice_name' : l1, 'datasource_name' : l2, 'database_name':l3}
    return sliceinfo

def change_dashboard(old_dshbd, new_dshbd_name, slice_name_list, datasource_name_list, datasource_id_list, database_name_list, database_id_list):
    
    d = modify_dashboard_name(old_dshbd, new_dshbd_name)
    d = modify_slices_info(d, database_name_list, datasource_name_list, datasource_id_list, slice_name_list)
    d = modify_datasources_info(d, database_id_list, database_name_list, datasource_name_list, datasource_id_list, slice_name_list)
    return d


def main():
    
    # with open(path_src, "r") as read_file:
    #     old_dshbd = json.load(read_file)

    # old_dshbd = args.old_dshbd
    # new_dshbd_name = args.new_dshbd_name
    # database_id_list = args.database_id_list
    # database_name_list  = args.database_name_list
    # datasource_id_list  = args.datasource_id_list
    # datasource_name_list = args.datasource_name_list
    # slice_name_list = args.slice_name_list

    d = change_dashboard(old_dshbd, new_dshbd_name, database_id_list, database_name_list, datasource_id_list, datasource_name_list, slice_name_list)

    # with open(path_dst, 'w') as json_file:
    #     json.dump(d, json_file)