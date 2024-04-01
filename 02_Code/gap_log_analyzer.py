
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 20 19:29:28 2023

@author: César Correa Feria
"""

#%% Import modules
import pandas as pd
import matplotlib.pyplot as plt
import math

#%% Config parameters
# Do you want to save the plot files to disk?
saveFiles = True
# Ok then...Where do you want to save them?
outputPath = r"..\03_Output"

#%% Functions
def replace_spaces(str):
    """
    Function to replace whitespaces with low dash
    inside single quotes. Required to be able to use whitespace
    as a column separator later on, because some names use both 
    whitespaces and low dashes as separators (bad practice!).

        str: input string
    """
    parts = str.split("'")
    for i in range(1,len(parts),2):
        parts[i] = parts[i].replace(' ', '_')
    return "'".join( parts )

def replace_prima(str):
    """
    Function to replace double single quotes ('') used in
    some names to denote prima (another bad practice!).

        str: input string
    """
    str = str.replace("''", "prima'")
    str = str.replace("' to", "prima to")
    return str

def extract (df, idCol, valCol, sort=2):
    """
    Function to extract main log features values (rate, reduction, flow and pressure balances) 
    into separate DataFrames. 

        df: any of the raw DataFrames already generated from the log file
        idCol: df column number containing item name (eg. well/item/node/pipe label) 
        valCol: df column number containing the variable to be extracted/plotted.
    
    Sorting only affects the columns order, aiming to display noisy items first.
        sort: 0 - sorts (ranks) on both standard deviation and number of value changes
        sort: 1 - sorts on standard deviation
        sort: 2 - sorts on number of value changes
    """
    items = [] #list container for item names
    series = [] #list container for series values
    for i, item in enumerate(df[idCol].unique()):
        serie = df[valCol][df[idCol]==item]
        serie = pd.to_numeric(serie)
        serie.reset_index(drop=True, inplace=True)
        items.append(item)
        series.append(serie)

    df = pd.DataFrame(series)
    df = df.transpose()
    df.columns = items

    #Sort columns according to:
    df.ffill(axis=0, inplace=True)
    if sort == 1: #stdDev of values
        df = df.iloc[:,(-df.std()).argsort()]
    elif sort == 2: #number of value changes
        df = df.iloc[:, (-(df.diff(axis=0) != 0).sum(axis=0)).argsort()]
    elif sort == 0: #both
        L = (-df.std().argsort()-((df.diff(axis=0) != 0).sum(axis=0)).argsort()).sort_values().index
        df = df.reindex(columns=L)
    else:
        print ("Not a valid sorting argument. No sorting performed.")

    return df

def plot(df, rows=10, figsize=(45,30), supTitle="Global Plot", subplotsTitle="Variable Name", save=True, saveName="sampleplot.png"):
    """
    A simple plotting function displaying all elements
    in the same plot. Picture file can be saved to the defined path.

        df: extracted -not raw- DataFrame.
        rows: maximum number of subplot rows. Reducing rows increases columns (resulting in narrower plots).
        figzise: global plot dimensions.
        supTitle: general title for the global plot.
        subplotsTitle: tag accompanying the item name for each subplot.
        saveName: file name if saving the plot to disk.
    """
    plots = len(df.columns)
    cols = math.ceil(plots/rows)
    fig = plt.figure(figsize=figsize, constrained_layout=True)

    for i, item in enumerate(df.columns):
        ax = fig.add_subplot(rows, cols, i+1)
        df.loc[:,item].plot().plot(ax=ax)
        ax.set_title(item + " - " + subplotsTitle)

    fig.suptitle(supTitle, fontsize=64)
    #fig.tight_layout()
    if saveFiles:    fig.savefig(outputPath + "\\" + saveName)
    plt.show()

#%% Load data
filePath = input("Input complete GAP log file path:")
if filePath.startswith('"') and filePath.endswith('"'):
    filePath = filePath[1:-1]

with open(filePath) as f:
    lines = f.readlines()

#%% Read text file
new_lines =  []
for line in lines:
    new_lines.append(replace_spaces(replace_prima(line)))

#%% All data into a DataFramre
df = pd.DataFrame(new_lines)

#%% Split into proper columns
df2 = df[0].str.replace(r'<(.\s)>', '_', regex=True).str.replace("'", "").str.split(" ", expand = True)

#%% Extract raw features dataframes
df_wells = df2.loc[df2[1]=='whp'].dropna(axis=1, how='all')
df_pipes = df2.loc[df2[0]=='Pipe'].dropna(axis=1, how='all')
df_rfs = df2.loc[df2[0]=='Variable'].dropna(axis=1, how='all')
df_eqn_flow = df2.loc[(df2[0]=='Solv') & (df2[9]=='flow')].dropna(axis=1, how='all')
df_eqn_pres = df2.loc[(df2[0]=='Solv') & (df2[9]=='pres')].dropna(axis=1, how='all')

#%% Extract features values into dataframes 
df_wellRates = extract(df_wells, 0, 6) #Gas rates
df_pipeRates = extract(df_pipes, 1, 13) #Gas Rates
df_redFact = extract(df_rfs, 2, 6)
df_presBal = extract(df_eqn_pres, 4, 11)
df_flowBal = extract(df_eqn_flow, 4, 11)

#%% Let's do some plotting
plot(df_wellRates, 10, (45,30), "Wells Gas Rate", "Gas Rate", saveFiles, "well_rates.png")
plot(df_pipeRates, 10, (45,30), "Pipes Gas Rate", "Gas Rate", saveFiles, "pipe_rates.png")
plot(df_redFact, 10, (45,30), "Wells Choke Adjustment", "Rate Reduction Factor", saveFiles, "reduction.png")
plot(df_presBal, 10, (45,30), "Pressure Balances", "Pressure Balance", saveFiles, "pres_balances.png")
plot(df_flowBal, 10, (45,30), "Flow Balances", "Flow Balance", saveFiles, "flow_balances.png")

# %%
