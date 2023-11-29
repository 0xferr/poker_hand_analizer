This tracker parses and imports hands played at 888poker. Calculates rake and profit for a specified period, and displays and saves a winning graph. It compute your Contributed Rake in the same way as poker room did it. Formula: Rake\ \* (your_investmets_in_pot/total_pot_size).

Rename config.example to config.ini. And fill it with your settings (your player_name, Import folder, postgre pasword/port etc.)

CLI for tracker:

options: -h, --help show this help message and exit --import [IMPORT_HH] Import hand history from the specified folder --results [RESULTS] Profit/Rake query in the format 'since|before=01/11/2023' or 'between=01/10/2023-20/10/2023'. Or 'cw'/'pw'/'cm'/'pm' for Current/Previous Week/Month --player PLAYER Specify Player name --chart [CHART] Show Chart --save [SAVE] Save Player_name and import_folder to config.ini

I'm planning to this features in future: Ability to filter omaha dealt hands by patter with option to export hand histories to file.

rake_calc.py is no database required version. Months that it will ask to input is the name of folder in start folder (2023/8 or 2023/11) as Nand2Note store it. You can specify it to avoid importing entire HH. In order to use it you should edit lines 18-23. Fill them with your player_name, UTC(GMT) difference, and handistory folder
