import pandas as pd
import matplotlib.pyplot as plt
from pandas.api.types import is_numeric_dtype
import os




"""_______________________________________________Load Input File________________________________________________________"""
#! Even if path exists, it still needs to be a csv and have a header row as well as value rows
path_exists = False
while path_exists == False:
    input_file = input("Please enter the full file path of the CSV you'd like to analyze:  ")
    if  os.path.exists(input_file) == True:
        path_exists = True
    else: print('ERROR: Instant Analyzer cannot detect a file at this location!')
##input_file = r"/Users/mattjacobson/Desktop/Example Data Sets/cars.csv"

#!The 'read_csv' function needs to be able to handle any type of codec package in which the csv is encoded (ex: UTF-8)
#there should at least be a prompt to the user to make sure the file is encoded with UTF-8

header_input_is_valid = False
while header_input_is_valid == False:
    number_of_header_rows = int(input('In which row do the headers exist?  (top row: type 0, second to top row: type 1, etc...):  '))
    try:
        df_raw = pd.read_csv(input_file,  low_memory=False, header = number_of_header_rows, encoding = "UTF-8")
        header_input_is_valid = True
    except:
        print('ERROR: Invalid header input!')

#find the extension type of the provided file path
file_extension = os.path.splitext(input_file)[1]
"""______________________________________________________END____________________________________________________________"""



"""_______________________________________________Optimize File_________________________________________________________________"""
df_optimized = df_raw.convert_dtypes(convert_integer=True) #auto convert data types to optimal data types 
df_optimized.columns = df_optimized.columns.str.replace(' ','_') #replace spaces in column names with underscores

#delete any columns that are completely blank
columns_dropped_count = 0
columns_dropped = []
for c in df_optimized.columns:
    if df_optimized[c].isnull().all(): #if every row is null for column c
        df_optimized.drop(c,axis=1, inplace = True)
    columns_dropped_count = columns_dropped_count + 1 #and log the count and names of dropped columns
    columns_dropped.append(c)
"""______________________________________________________END____________________________________________________________________"""



"""_______________________________________________Create Dummy Variables________________________________________________________"""
non_numeric_cols = [] #initiates list of columns to be converted to dummies
for cols in df_optimized: 
    if is_numeric_dtype(df_optimized[cols]) == False: #if (the data type of the currently iterated column being True) is FALSE
        if df_optimized[cols].duplicated().any(): #and the row contains at least one duplicate (meant to help prevent creating dummies off primary keys)
            if len(df_optimized[cols].unique()) <= 60: #if the number of unique elements in this column is less than 20
                non_numeric_cols.append(cols) #then add the currently iterated column to the list of non-numeric columns

df_optimized = pd.get_dummies(df_optimized, columns = non_numeric_cols)
"""______________________________________________________END____________________________________________________________________"""



"""_______________________________________________Correlation Matrix____________________________________________________________"""
correlation_matrix = df_optimized.corr() #Create correlation matrix

correlated_pairs = []
row_skipper = 0 #the addition of row skipper allows the iteration to stay below the diagonal of the corrrelation matrix, thus not creating duplicate rows
for column_name in correlation_matrix.columns:
    for row_name in correlation_matrix.index[row_skipper:]: 
        if str(column_name).split("_")[0] != str(row_name).split("_")[0]: #if the dummy prefix of first column is different from dummy prefix of second column
            correlated_pairs.append([column_name,row_name,correlation_matrix[column_name][row_name]]) #then append these items as a list to the corr pairs list
    row_skipper += 1

df_correlated_pairs = pd.DataFrame(correlated_pairs) #transform pairs list to df
df_correlated_pairs.columns = ["Field_1","Field_2", "Correlation"] #rename columns of pairs df
df_correlated_pairs = df_correlated_pairs[abs(df_correlated_pairs['Correlation']) < 1] #remove perfectly correlated pairs
df_correlated_pairs = df_correlated_pairs.sort_values(by=['Correlation'], key=abs, ascending=False) #sort pairs by desc corr values    
df_correlated_pairs = df_correlated_pairs.reset_index() #since the index was previously scrambled due to the sorting
df_correlated_pairs.drop('index', axis = 1, inplace=True) #resetting the index pushed the old index into a column. This drops that old column

#column shows the number of unique data pairs within each pair of columns in df_correlated_pairs
df_correlated_pairs['unique_pairs'] = None
for rows in range(len(df_correlated_pairs)):
    field_1 = df_correlated_pairs.loc[rows]['Field_1']
    field_2 = df_correlated_pairs.loc[rows]['Field_2']
    df_temp = df_optimized[field_1]
    unique_count = len(df_temp.drop_duplicates())
    #print(unique_count)
    df_correlated_pairs['unique_pairs'][rows] = unique_count
"""______________________________________________________END____________________________________________________________________"""


"""_______________________________________________Save/Print____________________________________________________________________"""
#Save df_optimized and corr matrix to same location but append original name with "_new" and "_correlated_pairs"
input_file_name_only = os.path.basename(input_file).split(".csv")[0]
input_file_parent_dir = os.path.join(dirname(input_file)) #returns the folder in which the input file is contained
new_folder_location = os.path.join(input_file_parent_dir + "/" + input_file_name_only + "_Analysis_Results") #creates the NAME of the directory of the new analysis subfolder
if not os.path.exists(new_folder_location): #if the dir of the new subfolder doesn't already exist, create it.
    os.makedirs(new_folder_location)

df_optimized.to_csv(new_folder_location+ "/" + input_file_name_only + "_optimized_csv.csv") #save these in the newly created subfolder
df_correlated_pairs.to_csv(new_folder_location + "/" + input_file_name_only + "_correlated_pairs.csv")
"""___________________________________________________END_______________________________________________________________________"""

"""___________________________________________________Plotting__________________________________________________________________"""
#!this needs to only show plots where there are many different values, not just a few
#find the 5 pairs with the highest correlations and plot them
plot_count = 0
rows = 0
while plot_count < 5:
    x_axis_field = (df_correlated_pairs.loc[rows]['Field_1'])
    y_axis_field = (df_correlated_pairs.loc[rows]['Field_2'])
    if ~(x_axis_field[:6] == 'dummy_' and y_axis_field[:6] == 'dummy_'): #don't compare dummies against dummies 
        df_optimized.plot(x=x_axis_field, y=y_axis_field, kind = 'scatter')
        plt.ticklabel_format(axis='both',style='plain')
        plt.savefig(new_folder_location+ "/" + input_file_name_only + "plot_" + str(plot_count))
        plot_count += 1
    rows += 1
"""______________________________________________________END____________________________________________________________________"""
