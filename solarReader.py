import pandas as pd
import numpy as np
import requests
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import *
import matplotlib.pyplot as plt

class solarsite:
    """
        This object retrieves data via the solaredge API.
        attributes:
        site_id: the id of the solar site (hard coded)
        api_key: the api key to get data from the solar site
        methods:
        init_data(): checks the connection and gets the install date and last valid date
        get_data(): gets data over a specified date range (given at initalization)
        filter_data(): quick filter of data for a given date
        plot_data(): a quick plotter for the data based on the hour of the day
        simpint(): integrates the selected time period to calculate total kWh produced
    """
    def __init__(self,*argv):
        #the site id and api key
        self.site_id = SITEID #site ID is a 6 character number
        self.api_key = 'ENTERKEY HERE'
        
        #check connection
        self.installation_date,self.last_update = self.init_data()
        
        #check if date range entered
        if len(argv)==0:
            #use the install/last update range to get data
            self.data = self.get_data(self.installation_date,self.last_update)
        elif len(argv)==2:
            #use the input dates and sampling frequency
            self.data = self.get_data(argv[0],argv[1])
        else:
            raise ValueError('Wrong number of input arguments.  Please use either none or three.')
            
    def init_data(self):
        """
        get the installation date and the last updated date to determine the operating range
        """
        r = requests.get('https://monitoringapi.solaredge.com/site/{1}/details?api_key={0}'.format(self.api_key,self.site_id))
        if r.status_code==200:
            background_data = r.json
            installation_date = pd.DataFrame.from_dict(r.json()).loc['installationDate','details']
            last_update = pd.DataFrame.from_dict(r.json()).loc['lastUpdateTime','details']
            print('The site was active from %s to %s.' % (installation_date,last_update))
            return installation_date,last_update
        else:
            raise ValueError('Connection Failed!')
    
    def get_data(self,start_date,end_date):
        """
        INPUTS:
        This function pulls data off the Solaredge server via it's API.
        start_date: First date to collect data from string of format: YYYY-MM-DD
        end_date: Last date to collect data from string of format: YYYY-MM-DD
        OUTPUTS:
        pandas DataFrame with requested data.  INDEX = Datetime, COLUMNS = 'Date','Time'(hrs),'value(W)'
        """
        #convert date strings to datetimes
        start_date_dt = dt.strptime(start_date, '%Y-%m-%d')
        end_date_dt = dt.strptime(end_date, '%Y-%m-%d')+relativedelta(days=+1) #add a day due to the nature of the api

        pdDF = pd.DataFrame()

        #need to sample one month at a time
        d1 = start_date_dt
        d2 = d1 + relativedelta(months=+1) # add a month
        while (end_date_dt+relativedelta(months=-1))>d1:

            r = requests.get('https://monitoringapi.solaredge.com/site/{1}/power?startTime={2} 00:00:00&endTime={3} 00:00:00&&api_key={0}'.format(self.api_key,self.site_id,d1.strftime('%Y-%m-%d'),d2.strftime('%Y-%m-%d')))
#energy     r = requests.get('https://monitoringapi.solaredge.com/site/{1}/energy?timeUnit={4}&endDate={3}&startDate={2}&api_key={0}'.format(self.api_key,self.site_id,d1.strftime('%Y-%m-%d'),d2.strftime('%Y-%m-%d'),time[sampling_freq]))
            tempDF = pd.DataFrame.from_dict(r.json()['power']['values'])
            if pdDF.shape[0]==0:
                pdDF = tempDF.copy()
            else:
                pdDF = pdDF.append(tempDF)
           
            d1 = d2 # add a day
            d2 = d1 + relativedelta(months=+1)

        d1 = d2 + relativedelta(months=-1)
        #energy r = requests.get('https://monitoringapi.solaredge.com/site/{1}/energy?timeUnit={4}&endDate={3}&startDate={2}&api_key={0}'.format(api_key,site_id,d1.strftime('%Y-%m-%d'), end_date_dt.strftime('%Y-%m-%d'),time[sampling_freq]))
        r = requests.get('https://monitoringapi.solaredge.com/site/{1}/power?startTime={2} 00:00:00&endTime={3} 00:00:00&&api_key={0}'.format(self.api_key,self.site_id,d1.strftime('%Y-%m-%d'),end_date_dt.strftime('%Y-%m-%d')))
        tempDF = pd.DataFrame.from_dict(r.json()['power']['values'])
        pdDF = pdDF.append(tempDF)    

        print('The site was active from %s to %s.' % (start_date,end_date))
        #do a bit of massaging of the date/time
        pdDF[['Date','Time']] = pdDF['date'].str.extract(r'(?P<Date>\d{4}-\d{2}-\d{2}) (?P<Time>\d{2}:\d{2}:\d{2})')
        pdDF['date']=pd.to_datetime(pdDF['date'])
        pdDF.set_index('date',inplace=True)
        pdDF = pdDF[['Date','Time','value']].copy()
        pdDF['Time'] = pdDF['Time'].str.extract(r'(\d{2})').astype(float)+(pdDF['Time'].str.extract(r'\d{2}:(\d{2})')).astype(float)/60+(pdDF['Time'].str.extract(r'\d{2}:\d{2}:(\d{2})')).astype(float)/3600
        
        #there are typically lots of NAs, so fill these as 0
        pdDF['value'] = pdDF['value'].fillna(0)
        return pdDF
    
    def filter_data(self,*argv):
        """
        Filters the data to match a given year/month/day
        INPUT
        argv (int)s where
        if len(argv)==1:
            argv[0] is either a year (YYYY) or month (MM) to match
        if len(argv)==2:
            argv[0] is a year and argv[1] a month YYYY,MM
        if len(argv)==3:
            argv[0] is a year, argv[1] a month YYYY,MM, argv[2] a month YYYY,MM,DD
        OUTPUT
        dataframe as filtered for the appropriate time
        """
        if len(argv)==1:
            #filter based on year or month (may contain multiple years/months)
            if argv[0] > 12: 
                #filter based on year
                filter_date = dt(argv[0],1,1)
                return self.data[(self.data.index).year==filter_date.year].copy()
            else:
                #filter based on month
                filter_date = dt(1900,argv[0],1)
                return self.data[(self.data.index).month==filter_date.month].copy()
        if len(argv)==2:
            #filter based on both
            filter_date = dt(argv[0],argv[1],1)
            return self.data[((self.data.index).year==filter_date.year)&((self.data.index).month==filter_date.month)].copy()
        if len(argv)==3:
            #filter based on year,month,day
            filter_date = dt(argv[0],argv[1],argv[2])
            return self.data[((self.data.index).year==filter_date.year)&((self.data.index).month==filter_date.month)&((self.data.index).day==filter_date.day)].copy()
            
    def plot_data(self,*argv):
        """
        Plots the median data by hour in a manner specified by the filter
        INPUT
        argv (int)s where
        if len(argv)==1:
            argv[0] is either a year (YYYY) or month (MM) to match
        if len(argv)==2:
            argv[0] is a year and argv[1] a month YYYY,MM
        if len(argv)==3:
            argv[0] is a year, argv[1] a month YYYY,MM, argv[2] a month YYYY,MM,DD
        OUTPUT
        a plot of the data
        """
        title = ''
        if len(argv)==1:
            #filter based on year or month (may contain multiple years/months)
            if argv[0] > 12: 
                #filter based on year
                filter_date = dt(argv[0],1,1)
                fdata = self.data[(self.data.index).year==filter_date.year].copy()
                title='Median Hourly Solar Generation for the Year: %d' % argv[0]
            else:
                #filter based on month
                filter_date = dt(1900,argv[0],1)
                fdata = self.data[(self.data.index).month==filter_date.month].copy()
                title='Median Hourly Solar Generation for the Month: %d' % argv[0]
        if len(argv)==2:
            #filter based on both
            filter_date = dt(argv[0],argv[1],1)
            fdata = self.data[((self.data.index).year==filter_date.year)&((self.data.index).month==filter_date.month)].copy()
            title='Median Hourly Solar Generation for the Month: %d in the Year: %d' % (argv[1],argv[0])
        if len(argv)==3:
            #filter based on year,month,day
            filter_date = dt(argv[0],argv[1],argv[2])
            fdata = self.data[((self.data.index).year==filter_date.year)&((self.data.index).month==filter_date.month)&((self.data.index).day==filter_date.day)].copy()
            title='Median Hourly Solar Generation for %d/%d/%d' % (argv[0],argv[1],argv[2])
        fig = plt.figure(figsize=(8,5),dpi=180)
        plt.plot(fdata.groupby('Time').median()['value'])
        plt.xlabel('Hours after Midnight')
        plt.ylabel('Median (W)')
        plt.title(title)
        pass
    def simpint(self,*argv):
        """
        A simple simpson's rule power integrator.
        INPUT:
        x - a dataframe with two columns TIME (datetime) and Value (Float) Watts
        OUTPUT:
        val - the integrated reading in kWh
        """
        int_data = self.filter_data(*argv)[['Time','value']]
        val = 0
        for i in range(int_data.shape[0]):
            if ((i%2)==1) & (i<(int_data.shape[0]-1)):
                timedel = (int_data.iloc[i+1,0]-int_data.iloc[i-1,0])
                area = (int_data.iloc[i-1,1]+4*int_data.iloc[i,1]+int_data.iloc[i+1,1])/6 #area under the curve
                val += timedel*area

        return np.round(val,3)
