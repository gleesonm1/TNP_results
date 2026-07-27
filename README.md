# TNP race results

This repository contains the code needed to process zwift racing results and maintain the TNP results page at:

https://tnp-results.streamlit.app/?event=La+Blanca&sheet=GC

## How to use
Feel free to copy the code to design your own app.

If you're looking to use this to process results from a TNP run series then contact me for access.

The code is hopefully quite simple. In each folder there should be a Python file that can be used to scrape results from Zwift Power. The code extensively uses the fantastic package ZPDataFetch (https://github.com/puckdoug/zpdatafetch). Before starting follow the instructions on the ZPDataFetch page for setting up you Zwift Power authorization (I suggest creating a new Python environment for this work).

Once your Zwift Power authorization has been entered, clone this repository onto your local machine. Using the terminal or command prompt navigate to the relevant folder (e.g., 'LaBlanca') and run the Python script located there. There are two options for running the script. Option one is to simply run the command

```
python LaBlancaProcessing.py 
```

This will process the results from ALL races listed in the .py file.

Alternatively (and this is much quicker) you can update the results of 1 or more races through the terminal/command prompt via:

```
python LaBlancaProcessing.py --mode  add --races 5604933 5604934
```

where 5604933 5604934 represent the Zwift Power race id of the races you want to update/scrape the results from.

Either method should update the overall results spreadsheet (in this case 'LaBlanca.xlsx'). Pushing this excel file to the main branch of this repository will automatically update the results page.
