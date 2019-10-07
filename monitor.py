import glob
import os
import json
import time

clear = lambda : os.system("clear")

time_limit = 60*6000*10

first_col = 16
sec_col = 45
third_col = 10

def size_formating(s, target_len, cut_end=False):
    while len(s)<target_len:
        s+=" "
    if len(s)>target_len and cut_end:
        s = s[0:target_len-3]+"..."
    return s


def launch_monitoring(extra_infos = True):
    files_dates = {}
    files_data = {}
    try:
        while True:
            root_path = os.path.split(__file__)[0]
            if root_path == "":
                root_path = "."
            files = glob.glob(root_path + "/logs/*.json")
            update=False
            for f_path in files:
                if f_path not in files_dates:
                    files_dates[f_path]=-1
                    files_data[f_path]=None
                modification_time = os.path.getmtime(f_path)
                if modification_time != files_dates:
                    update=True
                    with open(f_path, "r") as f:
                        data = json.load(f)
                    files_data[f_path] = data
                    files_dates[f_path] = modification_time
            if update:
                clear()
                current_time = time.time()
                for i, f_path in enumerate(sorted(list(files_data.keys()), key=lambda x: files_dates[x])):
                    identifier = str(files_data[f_path]["PID"])
                    if "HOST" in files_data[f_path]:
                        identifier += " " + files_data[f_path]["HOST"]
                    if current_time-files_dates[f_path]<time_limit or i == len(list(files_data.keys()))-1:
                        if len(files_data[f_path]["messages"]) == 1 and i != len(list(files_data.keys()))-1:
                            print(size_formating(identifier,first_col) +
                                  size_formating(files_data[f_path]["messages"][0], sec_col)+
                                  size_formating("[" +files_data[f_path]["STATUS"][-1]+ "]", third_col))
                        else:
                            print(size_formating(identifier, first_col) +
                                  size_formating(files_data[f_path]["messages"][0], sec_col))
                            print(size_formating("", first_col) +
                                  size_formating(files_data[f_path]["messages"][-1], sec_col)+
                                  size_formating("[" +files_data[f_path]["STATUS"][-1]+ "]", third_col))
                            if "loop_remaining_time" in files_data[f_path]["infos"]:
                                print(size_formating("", first_col) + size_formating("Remaining time :",sec_col) +
                                      size_formating(files_data[f_path]["infos"]["loop_remaining_time"],third_col))
                            if "GPU" in files_data[f_path]["infos"]:
                                print(size_formating("", first_col) +size_formating("Using GPU : ",sec_col) +
                                      size_formating("[" + ", ".join(files_data[f_path]["infos"]["GPU"])+"]",third_col))
                            if extra_infos:
                                for inf_key in list( files_data[f_path]["infos"].keys()):
                                    if inf_key != "GPU" and inf_key != "loop_remaining_time":
                                        print(size_formating("", first_col) +
                                              size_formating(inf_key.replace("_", " ") + " :",sec_col) +
                                              size_formating(str( files_data[f_path]["infos"][inf_key]),third_col))
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

launch_monitoring()