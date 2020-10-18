import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import *

class solarefficiency():
    lat = 43.656278 #site latitude
    long = -79.44037 #site longitude
    p1w = 12 #site 1 has 12 panels
    p1B = 37 #sloop of roof
    p1y = 165 #azimuthal rotation
    p2w = 9
    p2B = 33.75 #slope of roof
    p2y = 75 #azimuthal rotation
    
    def __init__(self,adate):
        """
        adate is a string of format 'YYYY-MM-DD HH:MM:SS'
        """
        day_dt = dt.strptime(adate[:10],"%Y-%m-%d") #convert to date time
        day0 = adate[:4]+'-01-01' #first day of the year
        day0_dt = dt.strptime(day0,"%Y-%m-%d")
        self.d = (day_dt-day0_dt).days #day of the year
        self.t = float(adate[11:13])+float(adate[14:16])/60 #time of day
        self.UTC = self.daylight(day_dt)
        #Longitude and Latitude for the location in Toronto, Canada

        self.EOT = self.EoT() #calculate the equation of time
        self.locSTM = self.LSTM() #calculate the local Standard Meridian time
        self.timecorr = self.TC() #calculate the time correciton factor
        self.lst = self.LST() #calculate the local standard time
        self.dec = self.declination_angle() #the declination angle
        self.HRA = self.hour_angle()  # the hour angle
        self.ea = self.elevation_angle() #the elevaiton angle of the sun
        self.azi = self.azimuth_angle() #the elevaiton angle of the sun
        self.atms = self.atmos() #the effect of the atmosphere on the sunlight intensity
        self.sol_eff1 = self.atms*self.p1w*self.solar_efficiency(self.p1B,self.p1y) #solarefficiency of first site
        self.sol_eff2 = self.atms*self.p2w*self.solar_efficiency(self.p2B,self.p2y) #solarefficiency of first site
        self.sol_eff_tot = (self.sol_eff1 + self.sol_eff2)
            
    def daylight(self,day):
        """
        Calculates the UTC for the given day
        """
        dlsstr = {"2017": dt.strptime("2017-03-12","%Y-%m-%d"),"2018": dt.strptime("2018-03-11","%Y-%m-%d"),"2019": dt.strptime("2019-03-10","%Y-%m-%d"),"2020": dt.strptime("2020-03-8","%Y-%m-%d")}
        dlsstp = {"2017": dt.strptime("2017-11-05","%Y-%m-%d"),"2018": dt.strptime("2018-11-04","%Y-%m-%d"),"2019": dt.strptime("2019-11-03","%Y-%m-%d"),"2020": dt.strptime("2020-11-01","%Y-%m-%d")}
        year = day.strftime("%Y-%m-%d")[:4]
        if (day>=dlsstr[year]) & (day<dlsstp[year]):
            return -4
        else:
            return -5
            
    def EoT(self):
        """
        The Equation of Time which accounts for eccentricity in the Earth's orbit and the Earth's axial tilt.
        Accurate to within 1/2 a minute.
        INPUT:
        d(int) - the number of days since the start of the year
        OUTPUT:
        minutes of correction (float)
        """
        if (self.d >= 0) & (self.d<367): #ensure the day is kosher
            B = np.radians(360/365*(self.d-81))
            EqofT = 9.87*np.sin(2*B)-7.53*np.cos(B)-1.5*np.sin(B)
            return EqofT
        else: #throw error
            raise ValueError('Date out of range.')
        
    def LSTM(self):
        """
        Local standard time meridian (time difference form meridian)
        INPUT:
        UTC(int): Time Zone varying from -12 to +14 
        OUTPUT:
        LSTM: in degrees
        """
        if (self.UTC >-13) & (self.UTC <15):
            return 15*self.UTC
        else:
            raise ValueError('UTC out of range.')
        
    def TC(self):
        """
        The Time Correction Factor which accounts for the variation 
        in local solar time within a given timezone due to the longitudinal
        spread of that timezone
        INPUTS:
        d(int): days since start of the year
        longitude(float): longitude of site
        UTC(int): Time Zone varying from -12 to +14 
        OUTPUTS:
        Time Correction Factor in minutes (float)
        """
        #TC = 4*(longitude-LSTM)+EoT
        return 4*(self.long-self.locSTM)+self.EOT

    def LST(self):
        """
        The local standard time which is the local time corrected for the variation 
        in local solar time within a given timezone due to the longitudinal
        spread of that timezone
        INPUTS:
        local_time(float): local time in hours after midnight (24 hour clock)
        time_corr(float): correction factor in minutes
        OUTPUTS:
        lst(float): local standard time in hours
        """
        return self.t+self.timecorr/60

    def declination_angle(self):
        """
        The declination angle of the sun (relative to the equator)
        INPUT:
        INPUT:
        d(int) - the number of days since the start of the year
        OUTPUT:
        angle(float) in degrees
        """
        if (self.d >= 0) & (self.d<367): #ensure the day is kosher
            dec = -23.45 * np.cos(np.radians(360/365*(self.d+10)))
            return dec
        else: #throw error
            raise ValueError('Date out of range.')
              
    def hour_angle(self):
        """
        The hour angle converts the local solar time into the number of degrees which 
        the sun moves across the sky.  It's 0 at solar noon (by definition)
        INPUT:
        localST(float): hours since midnight, local solar time
        OUTPUT:
        HRA (degrees)
        """
        return 15*(self.lst-12)
    
    def elevation_angle(self):
        """
        The elevation angle is the height of the sun in the sky
        for a particular location at a particular time and day of the year
        INPUTS:
        d: days after the start of the year
        lat(float): location latitude
        lon(float): location longitude
        utc(int): Time Zone varying from -12 to +14 
        t(float): time after midnight in hours
        OUTPUTS:
        elevation angle(float) in degrees
        """

        dec = np.radians(self.dec) #declination angle
        time_correction = self.timecorr #time correction factor
        local_solar_time = self.lst #local solar time
        HRA = np.radians(self.HRA) #hour angle
        latit = np.radians(self.lat) #latitude in radians
        alpha = np.arcsin(np.sin(dec)*np.sin(latit)+np.cos(dec)*np.cos(latit)*np.cos(HRA))
        return np.degrees(alpha)

    def azimuth_angle(self):
        """
            The elevation angle is the height of the sun in the sky
            for a particular location at a particular time and day of the year
            INPUTS:
            d: days after the start of the year
            lat(float): location latitude
            lon(float): location longitude
            utc(int): Time Zone varying from -12 to +14 
            t(float): time after midnight in hours
            OUTPUTS:
            elevation angle(float) in degrees
        """
        dec = np.radians(self.dec) #declination angle
        time_correction = self.timecorr #time correction factor
        HRA = np.radians(self.HRA) #hour angle
        latit = np.radians(self.lat) #latitude in radians
        azi = np.arccos((np.sin(dec)*np.cos(latit)-np.cos(dec)*np.sin(latit)*np.cos(HRA))/np.cos(np.radians(self.ea)))
        if (self.lst<12) | (HRA <0):
            return np.degrees(azi)
        else:
            return 360 -  np.degrees(azi)
    def atmos(self):
        """
        this function takes into account the impact of the atmposhere on the sunlight and
        it's varying pathlength throughit.
        """
        if self.ea <= 0: 
            AM = 99999999999
        else:
            AM = 1/np.cos(np.radians(90-self.ea))
        amp = AM**(.678)

        return 1.353*(.7**amp)
        
    
    def solar_efficiency(self,B,y):
        """
            The solar efficiency based on the sun's elevation angle(A), the panels tilt(B), the sun's azimuth angle (az) 
            and the panel's (y)
            INPUTS:
                A(float): the sun's elevation angle in degrees
                B(float): the panel's tilt in degrees
                az(float): the sun's azimuth angle in degrees
                y(float): the panel's azimuth angle in degrees
            OUTPUTS:
                the system efficiency 
        """
        A = self.ea
        az = self.azi

        if A < 0:
            #the sun has set
            return 0
        else:
            t1 = np.cos(np.radians(A))*np.sin(np.radians(B))*np.cos(np.radians(az-y))
            t2 = np.sin(np.radians(A))*np.cos(np.radians(B))
            if (t1+t2) >0:
                return t1+t2
            else:
                return 0