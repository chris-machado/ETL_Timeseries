import pandas as pd
import yaml 
import mysql.connector

# =============================================================================
# Import the data and prepare, deleting unused columns and rows, then transpose
#==============================================================================

prep_data = pd.DataFrame({})
for year in range(1992,2021):

# Define footer cutoff point
    if year <= 2000:
        cut_line = 47
    elif year <= 2016:
        cut_line = 45
    else:
        cut_line = 48
        
    # import file
    data = pd.read_excel('mrtssales92-present.xls', 
                          sheet_name=str(year),  
                          skiprows=3, 
                          skipfooter=cut_line)
    data = data.iloc[:,1:14]
    data.drop(range(1,9), axis=0, inplace=True)      # Drop rows of totals
    data.iloc[0,0] = 'dates'                         # Assign title to category column
    data['Kind of Business'].str.replace("\'", "")   # Remove apostrophes
 
    data_T = data.transpose()            #Transpose dataframe
    data_T.columns = data_T.iloc[0,:]    #Rename column headers to business type
    data_T = data_T.iloc[1:,:]           #Remove top row
 
 # ==== Reformat date to SQL standard =====   
 
    data_T['dates'] = data_T['dates'].str.split('.', expand=False)
    month = data_T['dates'].str[0]
    year = data_T['dates'].str[1]
    data_T.drop('dates', axis=1, inplace=True)
    
    month.replace('Jan', '01', inplace=True)
    month.replace('Feb', '02', inplace=True)
    month.replace('Mar', '03', inplace=True)
    month.replace('Apr', '04', inplace=True)
    month.replace('May', '05', inplace=True)
    month.replace('Jun', '06', inplace=True)
    month.replace('Jul', '07', inplace=True)
    month.replace('Aug', '08', inplace=True)
    month.replace('Sep', '09', inplace=True)
    month.replace('Oct', '10', inplace=True)
    month.replace('Nov', '11', inplace=True)
    month.replace('Dec', '12', inplace=True)

    date = [str(year[i]+'-'+month[i]+'-01') for i in range(0,12)]
    data_T.insert(0, 'Date', date)
    
  
 # ==== Clean empty values and join df =====  

    data_T.replace(['(S)','(NA)'], 0, inplace=True)
    prep_data = pd.concat([prep_data, data_T])
    
prep_data.reset_index(inplace=True, drop=True) # reset index after assembled
prep_data.to_csv('prepared_data.csv')          # Save cvs to pwd for later use


# =============================================================================
# Create database, table, and columns
#==============================================================================    

# connect to mysql server
db = yaml.safe_load(open('../db.yaml'))
config = {
    'user':     db['user'],
    'password': db['pwrd'],
    'host':     db['host'],
    'database': db['db']}
cnx = mysql.connector.connect(**config)
cnx.autocommit = True
cursor =cnx.cursor()

# Create query by defining db, table, pri key, and columns by looping over 
# the column titles 

cols = prep_data.columns
query = ("""
         DROP DATABASE IF EXISTS mrts; CREATE DATABASE mrts; USE mrts; 
         CREATE TABLE mrts_data (`id` SMALLINT NOT NULL AUTO_INCREMENT,  
                                 `Date` DATETIME NOT NULL,  
        """)

for item in cols:
    if item != 'Date':
        query += ('`%s` INT(9) DEFAULT NULL, ' % item) 
                                  
query += ('PRIMARY KEY (id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
cursor.execute(query, multi=True)

cursor.close()
cnx.close()


# =============================================================================
# Populate the Table
# =============================================================================
# Create the connection
cnx = mysql.connector.connect(**config)
cnx.autocommit = True                    # Important to alter the table 
cursor =cnx.cursor()   

# Iterate through each row and insert into db table 

for i, r in prep_data.iterrows():         
    rv = [i+1] + r.tolist()   # Combine with pri key 'id' and date
    query2 = ("""
              INSERT INTO mrts_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
              """)  
    cursor.execute(query2, rv)

# Disconnect      
cursor.close()
cnx.close()
# ================================== END ======================================


