
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import yaml 
import mysql.connector
# =============================================================================
# Define Functions   
# =============================================================================
def inflate (df, inflation):
    """ Adjusts dataframe values for inflation """
    inflated = pd.DataFrame([], index=df.columns)
    for i, row in df.iterrows():
        year = datetime.date(row[1]).year

        for y in inflation.loc[year:].values: 
            row[2:] *= (1+y)
    
        inflated = pd.concat([inflated, row], axis=1) 
    inflated = inflated.transpose()   
    return inflated

def make_plot (X, Y, Xlab, Ylab, Title, rotation=0, 
               color='blue', save=False):
    """ Makes a plot from 2 variables """
    fig = plt.figure()
    plt.plot(X,Y,color=color)
    plt.xlabel(Xlab)
    plt.xticks(rotation=rotation)
    plt.ylabel(Ylab)
    plt.title(Title)
    if save:
        name = Title[:10] + '.png'
        plt.savefig(name)
    plt.show()
    return fig

def sql_query (query, yaml_file, auto_commit=False):
    """ Connects to the sql server executes 
        a query and returns dataframe """
    db = yaml.safe_load(open(yaml_file))
    config = {
        'user':     db['user'],
        'password': db['pwrd'],
        'host':     db['host'],
        'database': db['db']}
    cnx = mysql.connector.connect(**config)
    if auto_commit:
        cnx.autocommit = True
    cursor = cnx.cursor()
    cursor.execute(query)
    
    data = []
    for row in cursor.fetchall() :
        data.append(row)
    cols =[i[0] for i in cursor.description]
    data = pd.DataFrame(data, columns=cols)

    cursor.close()
    cnx.close()
    return data
    
#==============================================================================
#    Compare inflation adjusted vs unadjusted
# =============================================================================

query = 'SELECT * FROM mrts_data'
inflation = pd.read_excel('usinflation.xls', sheet_name='usdata', index_col=(0))  

mrts_all = sql_query(query, '../mrts.yaml')
mrts_adj = inflate(mrts_all, inflation)


date = mrts_adj['Date']

# ========== Make plots for each business type ================================
# for i, col in mrts_adj.iloc[:,2:].iteritems():
#     make_plot(date, col, 'Year', 'USD in Millions',col.name)
# 
# for i, col in mrts_all.iloc[:,2:].iteritems():
#     make_plot(date, col, 'Year', 'USD in Millions',col.name, color='red')
# 

# =============================================================================
# Electronic Shopping Upward Trend
# =============================================================================
query = """
SELECT `id`, `Date`, `Electronic shopping and mail-order houses` FROM mrts_data
"""

eShoping = sql_query(query, '../mrts.yaml') 
eShoping_adj = inflate(eShoping, inflation)   

y = eShoping_adj['Electronic shopping and mail-order houses']/1000
make_plot(date, y,'Year','USD in Billions',
          'Electronic shopping and mail-order houses', color='teal')

# ==============Electronic Shopping seasonal Trend=============================

query = """SELECT month(`Date`) AS 'Month', 
sum(`Electronic shopping and mail-order houses`) AS 'Monthly Totals' 
FROM mrts_data 
GROUP BY month(`Date`);
"""
Month_totals = sql_query(query, '../mrts.yaml')

plt.bar(Month_totals['Month'],Month_totals['Monthly Totals']/1000, color='teal')
plt.xlabel('Month')
plt.xticks(range(1,13))
plt.ylabel('USD in Billions')
plt.title('Electronic Shopping and Mail-order Houses\n Total Spending Per Month')
plt.show()

# =============================================================================
# Percentages trend
# =============================================================================

totals = mrts_all.iloc[:,2:].sum(axis=1)
percent_eShopping = eShoping['Electronic shopping and mail-order houses']/totals*100

make_plot(date,percent_eShopping, 'Year', 'Percent %',
          'Electronic Shopping and Mail-order Houses\n as a Percent of Total Spending',
          color='teal')

# =============================================================================     
#  Rolling Time Window "Book Stores"
# =============================================================================
 
query = """
SELECT `id`, `Date`, `Book stores` FROM mrts_data
"""
books = sql_query(query, '../mrts.yaml')
books = inflate(books, inflation)
books['rolling'] = books.iloc[:,2:].rolling(3, center=True).mean()

make_plot(date, books['rolling'],'Year', 'USD in Millions',
          'Three Month Rolling Mean\n Book Store Spending', color='indigo')

x1 = books.iloc[313:338,1]
y1 = books.iloc[313:338,3]

x2 = books.iloc[169:194,1]
y2 = books.iloc[169:194,3]

make_plot(x1, y1,'Date', 'USD in Millions', 
               'Three Month Rolling Mean\n Book Store Spending', 
                rotation=45, color='indigo')

make_plot(x2, y2,'Date', 'USD in Millions', 
               'Three Month Rolling Mean\n Book Store Spending', 
                rotation=45, color='indigo')

# ============================================================================

make_plot(date, books['rolling'],'Year', 'USD in Millions', 
               'Three Month Rolling Average\n Book Store Spending', 
                rotation=0, color='indigo')
    