<h1>Solar Study</h1>
<p>The following project is my attempt to predict the solar output of the panels on my house in downtown Toronto using their installation information (number/wattage/orientation) and the historical weather forecast.  The results of this work are summarised in the jupyter notebook:  <b>Solar Study.ipynb</b><p>
  
<h3>File Inventory</h3>
  <ul>
    <li><b>solarReader.py:</b><p>A python class which interfaces with the SOLAREDGE API which can download current and historic data.  This also includes a variety of               filtering/plotting methods to facilitate data exploration</p></li>
    <li><b>solarPosition.py:</b><p>A python class with attributes *specific* to the installation on my house (panel number, orientation, wattage) and a variety of methods for   calcuating the sun's position in the sky for a particular time (hour+day+year).  The dot product of these solar vector and orientation vectors to give a metric that is proporitional to output (assuming no efficiency losses ie: without taking WEATHER or TEMPERATURE or PARTICULATE into consideration</p></li>
    <li><b>historical_weather_data.ipynb:</b><p>As it was challenging to find a free API, this sheet scrapes historical weather data for the toronto area from <a href=\"www.timeanddate.com\" title=\"A site for time and data and weather\">www.timeanddate.com</a>.  It then parses and cleans up the data and saves it into an SQL database for later use.</p></li>
    <li><b>Solar Study.ipynb:</b><p>The main analysis in which the data is all put together.  An EDA is performed an then the data is funneled into a random forest regressor.  The data is tested against a future datatime with good accuracy (albeit only on one timepoint)</p></li>
  </ul>
 
