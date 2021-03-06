#!c:/Users/Jake/AppData/Local/Programs/Python/Python38/python.exe

'''Script to control excution of getting data from JHU CSSE, adding all US data to a database, and updating a simple amcharts.com graph for florida COVID19 cases.'''

from datetime import date
import datetime
import requests

from rw_data import addNewDayData, commit, close
from update_chart import updateChart
from send_console_sms import Log
from configuration_vars import my_chart

__author__ = 'Jake Sutton'
__copyright__ = 'Copyright 2020, www.jakegsutton.com'

__license__ = 'MIT'
__email__ = 'jakesutton1249@gmail.com'
__status__ = 'Production'


#Creates a log instance for the entire program to use
log = Log()

print(log.logIt('Started Process...'))

#Dictionary for all states with data from the entire loaded file
us_data_dict = {}

#Gets date info needed. (This is set up so that 'today' is actually yesterday in relation to when the program is executed. 
#This is because the repository that the data is located is usually not uploaded until the next day in relation to the day the data is from)
#This program is designed to run in the morning the day after the day that the data is from.
today = date.today() - datetime.timedelta(days=1)
yesterday = today - datetime.timedelta(days=1)

formated_todays_date = date.strftime(today, '%m-%d-%Y')
formated_yesterdays_date = date.strftime(yesterday, '%m-%d-%Y')

#Used when parsing data, is replaced with \r if a \r is within the file (not using \r\n because it breaks other things)
nl = '\n'

#Used for createProvStateList fuction when \r\n is being used for line breaks
offset = 0


#Html request to JHU CSSE COVID-19 git repo
response = None
try:
    print(log.logIt('Getting data...'))
    response = requests.get('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/' + formated_todays_date + '.csv')
    response.raise_for_status()
except requests.HTTPError as e:
    print(log.logIt(str(e) + ' Looking for data elsewhere...'))
    try:
        response = requests.get('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/' + formated_yesterdays_date + '.csv')
    except requests.exceptions.RequestException as e:
        print(log.logIt('NO DATA FOUND... YESTERDAYS FILE MUST NOT EXIST... FATAL ERROR...'))
        raise SystemExit(e)


#Get text from request       
data = response.text

#Check for \r and change nl to \r and offset to 1 if true
if '\r' in data:
    nl = '\r'
    offset = 1


def createProvStateList():
    '''Function to create a list of all the province/states in the data set.'''
    l = []
    for i,d in enumerate(data):
        if i < len(data)-1 and d == nl:
            l.append(data[i+1+offset : data.index(',', i)])
    return l


#Grabbing some data and putting it in lists (setup for generating dictionaries)
data_categories = data[0 :  data.index(nl)].split(',')
data_categories_2 = data[data.index(',')+1 : data.index(nl)].split(',')
province_state_list = createProvStateList()


def generateUSDict():
    '''Generates a dictory with all data from the file.'''
    us_data = []

    for state in province_state_list:
        if data.find(nl, data.index(state)) == -1:
            us_data.append(data[data.index(state)+len(state)+1 : ].split(','))
        else:
            us_data.append(data[data.index(state)+len(state)+1 : data.index(nl, data.index(state))].split(','))
    for i, key in enumerate(province_state_list):
        us_data_dict[key] = {}
        for cat in data_categories_2:
            for val in us_data[i]:
                us_data_dict[key][cat] = val
                us_data[i].remove(val)
                break


#Calls the fuction to create the main data dictionary
generateUSDict()

#Calls fuction in store_data module to store data that is in us_data_dict in remote sql server
addNewDayData(us_data_dict,today)

#Commits changes to the datebase
commit()

#Calls function that executes selenium commands to add data from server to my amcharts.com Florida COVID19 cases chart 
updateChart(today)

#Closes the database connection
close()

print(log.logIt('Process complete...'))
print(log.logIt('Chart: ' + my_chart))
print(log.logIt('Time Completed: ' + date.strftime(datetime.datetime.now(), '%m/%d/%Y, %H:%M:%S') + ' America/New_York'))

#Sends a message to my phone that contains the log
log.send()

