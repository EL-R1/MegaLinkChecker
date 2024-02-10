import requests
import random
import json
import re
from bs4 import BeautifulSoup
import time

REGEX = "https://mega\.nz/((folder|file)/([^#]+)#(.+)|#(F?)!([^!]+)!(.+))"

# GET Current cache data 
def get_files_descriptions(url):
    response = requests.get(url)
    time.sleep(0.001)
    soup = BeautifulSoup(response.text, 'html.parser')
    og_description_tag = soup.find('meta', property='og:description')
    if og_description_tag:
        og_description = og_description_tag['content']
        
        # Extract file count and folder count from description
        if "files" in og_description and "subfolders" in og_description:
            file_count_str, _, folder_count_str = og_description.partition("files and ")
            folder_count_str = folder_count_str.split()[0]
            file_count = int(file_count_str)
            folder_count = int(folder_count_str)
        elif "files" in og_description:
            file_count_str = og_description.split()[0]
            file_count = int(file_count_str)
            folder_count = 0
        elif "subfolders" in og_description:
            folder_count_str = og_description.split()[0]
            folder_count = int(folder_count_str)
            file_count = 0
        else:
            file_count = 0
            folder_count = 0
    else:
       print("No details on the files found")
    return {'description_nb_files': file_count, 'description_nb_folders': folder_count}

# Get IDs of empty folders (same as get_ids_of_empty_folders)
def check_empty_folders(data, empty_folders_list=None):
    if empty_folders_list is None:
        empty_folders_list = []

    for key, value in data.items():
        if isinstance(value, dict) and 'nb_files' in value and 'nb_folders' in value:
            if value['nb_files'] == 0 and value['nb_folders'] == 0:
                empty_folders_list.append(key)
            if 'folders' in value:
                check_empty_folders(value['folders'], empty_folders_list)
    
    return empty_folders_list

# Get IDs of empty folders (same as check_empty_folders)
def get_ids_of_empty_folders(obj):
    ids = []
    for id_, data in obj.items():
        if data.get('folders') == {} and data.get('files') == []:
            ids.append(id_)
            #print(data, end="\n\n")
        elif data.get('folders'):
            ids.extend(get_ids_of_empty_folders(data['folders']))
    return ids

# Order data
def order_data(folders, parent=None):
  output = {}
  # Filter by parent
  filtered = { k: v for k, v in folders.items() if v["parent"] == parent }
  
  for folder_id, folder in filtered.items():
    # Copy folder data
    output[folder_id] = folder["data"].copy()
    # Use recusive to get childrens
    output[folder_id]["folders"] = order_data(folders, folder_id)
  
  return output

# Format data
def format_data(data):
  folders = {}
  
  # Fetch all folders
  for root_item in data:
    for item in root_item.get("f", []):
      # Si n'est pas un dossier skip l'itération
      if item["t"] != 1:
        continue
      folder_id =  item["h"]
      folder_parent_id = item["p"]
     
      if folder_parent_id not in folders:
        folders[folder_parent_id] = {
          "parent": None,
          "data": { "files": [], "definition": item }
        }
      folders[folder_id] = {
        "parent": folder_parent_id,
        "data": { "files": [], "definition": item }
      }
      
  # Fetch all files
  for root_item in data:
    for item in root_item.get("f", []):
      # Si n'est pas un fichier skip l'itération
      if item["t"] != 0:
        continue
      
      folders[item["p"]]["data"]["files"].append(item)
      
  # Order everyting and return
  return order_data(folders)

# Write size with byte
def write_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"
    elif size < 1024 ** 4:
        return f"{size / (1024 ** 3):.2f} GB"
    else:
        return f"{size / (1024 ** 4):.2f} TB"

# Replace size with write_size method
def remplace_size(objet):
    for cle, valeur in objet.items():
        if isinstance(valeur, dict):
            remplace_size(valeur)
        elif cle == 'size':
            objet[cle] = write_size(valeur)
            
# Sort by size before formatting size
def sort_by_size(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = sort_by_size(value)
        if 'folders' in obj:
            obj['folders'] = dict(sorted(obj['folders'].items(), key=lambda x: x[1].get('size', 0), reverse=True))
    return obj
    
# Create new objet with number of files, folders et size for all of them
def update_params(obj):
    if isinstance(obj, dict):
        if 'definition' in obj and 'files' in obj and 'folders' in obj:
            obj['size'] = sum(int(file.get('s', 0)) for file in obj['files'])
            obj['nb_files'] = len(obj['files'])
            obj['nb_folders'] = len(obj['folders'])
            # Rearrange keys at the top
            obj = {'size': obj['size'], 'nb_files': obj['nb_files'], 'nb_folders': obj['nb_folders'], **obj}
        for key, value in obj.items():
            obj[key] = update_params(value)
            # Updating size for parent objects
            if key == 'folders':
                for folder in value.values():
                    obj['size'] = obj.get('size', 0) + folder.get('size', 0)
        # Delete the 'definition' and 'files' keys
        obj.pop('definition', None)
        obj.pop('files', None)
    return obj

# Calculate total of files and folders
def calculate_totals(data):
    total_nb_files = 0
    total_nb_folders = 0

    # Browse object elements
    for key, value in data.items():
        # If the item is a folder
        if isinstance(value, dict) and 'nb_files' in value and 'nb_folders' in value:
            total_nb_files += value['nb_files']
            total_nb_folders += value['nb_folders']
            # If the folder has subfolders, recursively calculate the total
            if 'folders' in value:
                sub_totals = calculate_totals(value['folders'])
                total_nb_files += sub_totals['total_nb_files']
                total_nb_folders += sub_totals['total_nb_folders']

    return {'total_nb_files': total_nb_files, 'total_nb_folders': total_nb_folders}

# Mega checker base 
def mega_checker(url: str) -> bool:
    if "#F!" in url:
      url = url.replace("#F!", "folder/")
      url = url.replace("!", "#")
    elif "#!" in url:
      url = url.replace("#!", "file/")
      url = url.replace("!", "#")
    
    if not bool(re.search(REGEX, url)):
        return print("? - Improper link : "+url+"\n")
        
    url_parts = url.split("/")
    if len(url_parts) > 4:
        if "#" in url_parts[4]:
            link_id = url_parts[4].split("#")[0]
        else:
            link_id = url_parts[4]
    else:
        return print("? - Improper link : "+url+"\n") 
      
    if url.split("/")[3] == "folder":
        payload = {'a': 'f', 'c': 1, 'r': 1, 'ca': 1}
    else:
        payload = {'a': 'g', 'p': link_id}

    sequence_num = random.randint(0, 0xFFFFFFFF)

    response = requests.post(
        f"https://g.api.mega.co.nz/cs?id={sequence_num}&n={link_id}",
        data=json.dumps([payload])
    ).json()
    #print('https://g.api.mega.co.nz/cs?id='+str(sequence_num)+'&n='+str(link_id))
    
    if not type(response) is int:
        output = format_data(response)
        
        # Tree structure with folders, files and size recursively
        structure_with_files_folders_and_size = update_params(output) # create a new object, with folders and files recursively
        sort_by_size(structure_with_files_folders_and_size) # sort all files and folers by size value
        remplace_size(structure_with_files_folders_and_size) # Format size to write it with byte
        total = calculate_totals(structure_with_files_folders_and_size) # get the total numbers of files and folders
        print(structure_with_files_folders_and_size) # print the entire tree structure
        print("folders : "+str((total["total_nb_folders"]-1))+" files : "+str(total["total_nb_files"])) # display total number of files and folders
       
        # # If you want comparaison between description and current API parsed uncomment that, but it will takes just a bit more time
        # #Compare description and API results
        # description = get_files_descriptions(url)
        # if not (total["total_nb_files"] == description["description_nb_files"]):
        #   print("! - Differents files :\nAPI : "+str(total["total_nb_files"])+"\nDescription : "+str(description["description_nb_files"]))  
        # if not ((total["total_nb_folders"]-1) == description["description_nb_folders"]):
        #   print("! - Different folders :\nAPI : "+str(total["total_nb_folders"])+"\nDescription : "+str(description["description_nb_folders"]))  
        
        #Return empty folders
        ids_vides = check_empty_folders(output) or get_ids_of_empty_folders(output)
        if not ids_vides:
          return print("✓ - : "+url+"\n")
        else :
          return print("?✓ Empty folders :", ids_vides, "- "+url+"\n")
    else:
      return print("✗ - Dead : "+url+"\n")

#mega_checker("link")
