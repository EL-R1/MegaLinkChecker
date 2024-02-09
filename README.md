# MegaLinkChecker.py
Python based tool to check if mega.nz shared link is dead or not\
Big thanks to the original script [writter](https://github.com/snoofox/MegaLinkChecker.py)

# Updates
This script can be run on trinket as live coding.\
The only command you'll have to use is `mega_checker(link)` 

###  I added few things : 
 - If a link is not correctly written (don't match with regexs in the code)\
 => `? - Improper link : link`
 - If a valid links have empty folders, and it'll display all the ids of the folders\
 => `?✓ Empty folders : ['id_folder_1', 'id_folder_2', 'id_folder_3', 'id_folder_4', ...] - link`
 - It can see the difference between the definition of the html of mega (what embed such as in discord or with parsing the html you'll get) and the current api result (it can be not accurate specially with recent extremly files, i don't really recommand that, it will be much longer to execute on top of that)
 - It can show you a complete tree structure of the mega folder with or without all the definitions (you can remove the obj.pop if you want) :\
 =>
 ```json
 {
    "root_of_the_root_folder": {
        "size": "7.62 GB",
        "nb_files": 0,
        "nb_folders": 1,
        "root_mega_folder": {
            "id_folder_1": {
                "size": "7.62 GB",
                "nb_files": 0,
                "nb_folders": 6,
                "folders": {
                    "id_subfolder_1": {
                        "size": "6.60 GB",
                        "nb_files": 13,
                        "nb_folders": 0,
                        "folders": {}
                    },
                    "id_subfolder_2": {
                        "size": "1.02 B",
                        "nb_files": 7,
                        "nb_folders": 0,
                        "folders": {}
                    }
                }
            }
        }
    }
}
 ```
 If you want you can get all the definition of files and folders

---
If you have any ideas to optimise or to add some features or something else, don't hesitate
