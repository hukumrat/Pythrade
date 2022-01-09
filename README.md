# Pythrade - Accurate Trading in your stead! <br>
Pythrade can be tought as a guide for your tradements.<br>

### Description<br>
Pythrade merges RSI, MACD and Bollinger Bands indicators on one graph. Also indicates Golden Crosses and Death Crosses on graph while showing all possibilities according to Indicators individually and weighted mean Indicators' possibilities in HoverBox.<br>

### Getting Started<br>
### Dependencies<br>
* Python 3.
* pip for installing Django Module are required to run and use this project.<br>
### Installing<br>
* Install Python3.<br>
* Install Django Module.<br>
* In project folder, execute 'python manage.py runserver' command.<br>
* You will see a message that you can load the project on 'http://127.0.0.1:8000/' or 'http://localhost:8000/'<br>
* Login admin panel with 'http://127.0.0.1:8000/admin' or 'http://localhost:8000/admin' links.<br>
* Default username and password is admin:admin. 
  * Account can be created and superuser authority can be given in 'AUTHENTICATION AND AUTHORIZATION - Users' section.<br>
  * Also superuser account can be created executing 'python manage.py createsuperuser' command.<br>
* Add a coin symbol like BTC, ETH ADA etc.
* Go to homepage. Coins' -which be added in admin panel- market datas will be located in a table.
* Click 'Analysis' button which is in last column of table. Analysis page will be loaded. 
### Version History
* 1.0<br>
  * Initial relase.<br>
### Acknowledgments:
Tools has been used:<br>
* Yahoo-Finance (yfinance) library to get market datas.<br>
* Plotly library to sketch graph according to processed datas and manage it.<br>
* TA-Lib library to calculate indicators' values.<br>
* Numpy library to calculate high-level mathematical functions and operate large series which consists of market datas.<br>
* Pandas library to manipulate numerical tables and time series.<br>

For Designing:<br>
* Bootstrap.<br>
