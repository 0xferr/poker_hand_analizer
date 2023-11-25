This project isn't finished yet. tracker.py for now just parse handhistory from 888poker and import in database. 
I'm planning to this features in future: 
  1) Rake calculation.
  2) Graph plotting your profit
  3) Ability to filter omaha dealt hands by patter with option to export that hand histories

rake_calc.py is redy to use. And it doesn't needed postrgeSQL 
This script works only with 888poker hand history. It compute your Contributed Rake in the same way as poker room did it. Formula: Rake\*(your_investmets_in_pot/total_pot_size). Also it shows your prifit according provided hand history. Months that it will ask to input is the name of folder in start folder (2023/8 or 2023/11) as Nand2Note store it. You can specify it to avoid importing entire HH. Or simply specify it in START_DIR.
