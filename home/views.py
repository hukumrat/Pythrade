#Django'nun ihtiyaç duyduğu varsayılan kütüphaneler.
from django.shortcuts import render
from requests import Request, Session

#Test aşamasında verileri işlemek ve API'den gelen çok yüksek sayıları simplify etmek için gerekli kütüphaneler.
import json
from json import encoder
import pprint
from math import floor 

#Analiz ve Grafik için gerekli kütüphaneler.
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import talib
import pytz
from plotly.offline import plot
from plotly.subplots import make_subplots
from datetime import datetime


from requests.sessions import session

from home.models import coin_symbol

magnitudeDict={0:'', 1:'Bin', 2:'Milyon', 3:'Milyar', 4:'Trilyon', 5:'Quadrillion', 6:'Katrilyon', 7:'Sekstilyon', 8:'Septilyon', 9:'Oktilyon', 10:'Nonilyon', 11:'Desilyon'}
def simplify(num):
    num=floor(num)
    magnitude=0
    while num>=1000.0:
        magnitude+=1
        num=num/1000.0
    return(f'{floor(num*100.0)/100.0} {magnitudeDict[magnitude]}')

class Coin:
    def __init__(self, name, symbol, price, percent_change_24h, percent_change_7d, market_cap, volume_24h, circulating_supply):
        self.name = name
        self.symbol = symbol
        self.price = price
        self.percent_change_24h = percent_change_24h
        self.percent_change_7d = percent_change_7d
        self.market_cap = market_cap
        self.volume_24h = volume_24h
        self.circulating_supply = circulating_supply

def index(request):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'#CoinMarketCap API Linki.

    #API adresinin ayarlarının tutulduğu sözlük.
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '3058b5ad-f00d-4bb9-9769-a8d2d1ddfbbe'#CoinMarketCap API Key
    }

    #API'dan hangi verilerin hangi paritede geleceğini belirten sözlük.
    parameters = {
        'symbol': '',
        'convert': 'USD'
    }
    
    #Admin paneli üzerinden analiz edilmek istenen ve veri tabanına kaydedilen coin sembolleri.
    symbols = coin_symbol.objects.all()
    coins = []

    #Veri tabanındaki her bir sembol için ayrı ayrı verilerin çekilip gerekli bilgileri JSON formatında listeye ekleyip client-side'a gönderilmesi.
    for symbol in symbols:
        parameters["symbol"] = symbol
        session = Session()
        session.headers.update(headers)
        response = session.get(url, params=parameters)
        if json.loads(response.text)['status']['error_message'] == None: #Veri tabanındaki sembollerin yanlış girilmesi durumunda kontrolünün sağlanması.
            name = json.loads(response.text)['data'][str(symbol).upper()]['name']
            symbol = json.loads(response.text)['data'][str(symbol).upper()]['symbol']
            price = round(json.loads(response.text)['data'][str(symbol).upper()]['quote']['USD']['price'], 2)
            percent_change_24h = round(json.loads(response.text)['data'][str(symbol).upper()]['quote']['USD']['percent_change_24h'], 2)
            percent_change_7d = round(json.loads(response.text)['data'][str(symbol).upper()]['quote']['USD']['percent_change_7d'], 2)
            market_cap= simplify(json.loads(response.text)['data'][str(symbol).upper()]['quote']['USD']['market_cap'])
            volume_24h = simplify(json.loads(response.text)['data'][str(symbol).upper()]['quote']['USD']['volume_24h'])
            circulating_supply = simplify(json.loads(response.text)['data'][str(symbol).upper()]['circulating_supply'])
            coin = Coin(name, symbol, price, percent_change_24h, percent_change_7d, market_cap, volume_24h, circulating_supply)
            coins.append(coin)
            #pprint.pprint(json.loads(response.text))
        else:
            continue

    return render(request, "index.html", {"coins": coins})


def analysis(request, symbol):
    symbol_USD = symbol + "-USD" #Yahoo Finance'den verisi çekilecek kripto paranın USD paritesi ile birleştirilmiş sembolünün oluşturulması.
    data = yf.download(tickers=symbol_USD, period='1mo', interval='1h') #Yahoo Finance'den son 7 günün verilerini 1 saatlik aralıklarla alınması.
    #pd.set_option('display.max_rows', data.shape[0]+1)
    pd.options.display.float_format = '{:,.2f}'.format
    pd.set_option('mode.chained_assignment', None)
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    data.index = data.index.tz_convert(istanbul_tz)
    

    if "Empty DataFrame" in str(data): #Admin panelinden eklenen sembollerin Yahoo Finance'te bulunamaması şartı. 
        symbol_USD = symbol + "1-USD" #Kripto para sembolüne '1' eklenerek tekrar bir arama yapılması.
        data = yf.download(tickers=symbol_USD, period='1mo', interval='1h') #Değiştirilmiş sembol ile alınan son 7 günün 1 saatlik aralıklı verilerinin alınması.

    data['rsi_70'] = '70' #RSI indikatöründe (2. satırdaki grafikte) aşırı alım seviyesini (70) horizontal line olarak belirtmek için data sözlüğüne sabit 70 değerinin eklenmesi.
    data['rsi_30'] = '30' #RSI indikatöründe (2. satırdaki grafikte) aşırı satış seviyesini (30) horizontal line olarak belirtmek için data sözlüğüne sabit 30 değerinin eklenmesi.
    data['macd_0'] = '0' #MACD indikatöründe (3. satırdaki grafikte) sıfır seviyesini (0) horizontal line olarak belirtmek için data sözlüğüne sabit 0 değerinin eklenmesi.

    #ema20 = talib.MA(data['Close'], 20)
    ema50 = talib.MA(data['Close'], 50)
    #ema100 = talib.MA(data['Close'], 100)
    ema200 = talib.MA(data['Close'], 200)
    goldenCross = (ema50<ema200) & (ema50.shift(-1)>=ema200.shift(-1))
    deathCross = (ema50>ema200) & (ema50.shift(-1)<=ema200.shift(-1))
    data['ema50'] = ema50
    data['ema200'] = ema200
    data['goldenCross'] = goldenCross
    data['deathCross'] = deathCross
    goldenCross_json = json.loads(data[goldenCross].to_json())['goldenCross']
    deathCross_json = json.loads(data[deathCross].to_json())['deathCross']
    data_ema = data[['ema50', 'ema200', 'goldenCross','deathCross']]
    goldenCross_data = data_ema[(data_ema['goldenCross'] == True)]
    deathCross_data = data_ema[(data_ema['deathCross'] == True)]
    goldenCross_data_json = json.loads(goldenCross_data.to_json())
    deathCross_data_json = json.loads(deathCross_data.to_json())

    rsi = talib.RSI(data['Close']) #TA-Lib kullanılarak Yahoo Finance'den çekilen kripto para verilerine göre kapanış fiyatlarını kullanarak timestamplere göre RSI seviyelinin hesaplanması.
    rsiSell = (rsi>70) & (rsi.shift(-1)<=70) #RSI 70 seviyesini üstten kesen noktanın hesabı.
    rsiBuy = (rsi<30) & (rsi.shift(-1)>=30) #RSI 30 seviyesini alttan kesen noktanın hesabı.
    data['rsi'] = rsi #RSI değerlerinin data sözlüğüne yazdırılması.
    data['rsiSell'] = rsiSell #RSI indikatörüne göre sat sinyallerinin data sözlüğüne yazdırılması.
    data['rsiBuy'] = rsiBuy #RSI indikatörüne göre al sinyallerinin data sözlüğüne yazdırılması.
    rsiSell_json = json.loads(data[rsiSell].to_json())['rsiSell'] #RSI indikatörüne göre sat sinyallerinin key:value = timestamp:true teğerlerinin json formatında tutulması.
    rsiBuy_json = json.loads(data[rsiBuy].to_json())['rsiBuy'] #RSI indikatörüne göre al sinyallerinin key:value = timestamp:true teğerlerinin json formatına tutulması.
    data_rsiBuy = data[['rsi', 'rsiBuy']]
    data_rsiSell = data[['rsi', 'rsiSell']]
    data_rsi = data[['rsi', 'rsiBuy', 'rsiSell']]
    data_rsi['performance_percent'] = np.where(rsi<50, (100 - rsi) * 0.85, rsi * 0.85)
    rsiSell_data = data_rsiSell[(data_rsiSell['rsiSell'] == True)]
    rsiBuy_data = data_rsiBuy[(data_rsiBuy['rsiBuy'] == True)]
    rsiSell_data_json = json.loads(rsiSell_data.to_json())
    rsiBuy_data_json = json.loads(rsiBuy_data.to_json())
    data_rsi[['rsi', 'rsiBuy', 'rsiSell', 'performance_percent']] = data_rsi[['rsi', 'rsiBuy', 'rsiSell', 'performance_percent']].applymap('{:,.2f}'.format)

    upperband, middleband, lowerband = talib.BBANDS(data['Close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    basis = talib.SMA(data['Close'], timeperiod=20)
    dev = 2 * talib.STDDEV(data['Close'], timeperiod=20)
    upper = basis + dev
    lower = basis - dev
    crossunder = (data['Close']>upper) & (data['Close'].shift(-1)<=upper.shift(-1))
    crossover = (data['Close']<lower) & (data['Close'].shift(-1)>=lower.shift(-1))
    data['bbandle'] = crossover
    data['bbandse'] = crossunder
    data_bbandle = data[['Low', 'bbandle']]
    data_bbandle['performance'] = np.where(abs(data['Close'])<abs(lower), abs(lower/data['Close']), abs(data['Close']/lower))
    data_bbandle['performance_percent'] = np.where((data_bbandle['performance']<=1.02) & (data_bbandle['performance']>=0.98), (-212500 * ((data_bbandle['performance'] - 1)**2) + 85), 0)
    data_bbandse = data[['High', 'bbandse']]
    data_bbandse['performance'] = np.where(abs(data['Close'])>abs(lower), abs(data['Close']/upper), abs(upper/data['Close']))
    data_bbandse['performance_percent'] = np.where((data_bbandse['performance']<=1.02) & (data_bbandse['performance']>=0.98), (-212500 * ((data_bbandse['performance'] - 1)**2) + 85), 0)
    bbandle_data = data_bbandle[(data_bbandle['bbandle'] == True)]
    bbandle_data_json = json.loads(bbandle_data.to_json())
    #data_bbandse = data[['High', 'bbandse']]
    bbandse_data = data_bbandse[(data_bbandse['bbandse'] == True)]
    bbandse_data_json = json.loads(bbandse_data.to_json())
    data_bbandse[['High', 'bbandse', 'performance', 'performance_percent']] = data_bbandse[['High', 'bbandse', 'performance', 'performance_percent']].applymap('{:,.2f}'.format)
    data_bbandle[['Low', 'bbandle', 'performance', 'performance_percent']] =  data_bbandle[['Low', 'bbandle', 'performance', 'performance_percent']].applymap('{:,.2f}'.format)

    macd, macdsignal, macdhist = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    macdSell = (macd>0) & (macdsignal>0) & (macd>macdsignal) & (macd.shift(-1)<=macdsignal.shift(-1)) & (macdhist>0) & (macdhist.shift(-1)<=0)
    macdBuy = (macd<0) & (macdsignal<0) & (macd<macdsignal) & (macd.shift(-1)>=macdsignal.shift(-1)) & (macdhist<0) & (macdhist.shift(-1)>=0)
    data['macd'] = macd
    data['macdsignal'] = macdsignal
    data['macdSell'] = macdSell
    data['macdBuy'] = macdBuy
    macdSell_json = json.loads(data[macdSell].to_json())['macdSell'] 
    macdBuy_json = json.loads(data[macdBuy].to_json())['macdBuy'] 
    data_macdBuy = data[['macd', 'macdsignal', 'macdBuy']]
    data_macdSell = data[['macd', 'macdsignal', 'macdSell']]
    data_macdSell['performance'] = np.where(abs(macd)>abs(macdsignal), abs(macd/macdsignal), abs(macdsignal/macd))
    data_macdSell['performance_percent'] = np.where((data_macdSell['performance']<=2) & (data_macdSell['performance']>=0), (-85 * (data_macdSell['performance']**2) + 170 * (data_macdSell['performance'])), 0)
    data_macdBuy['performance'] = np.where(abs(macd)<abs(macdsignal), abs(macdsignal/macd), abs(macd/macdsignal))
    data_macdBuy['performance_percent'] = np.where((data_macdBuy['performance']<=2) & (data_macdBuy['performance']>=0), (-85 * (data_macdBuy['performance']**2) + 170 * (data_macdBuy['performance'])), 0)
    macdBuy_data = data_macdBuy[(data_macdBuy['macdBuy'] == True)]
    macdSell_data = data_macdSell[(data_macdSell['macdSell'] == True)]
    macdBuy_data_json = json.loads(macdBuy_data.to_json())
    macdSell_data_json = json.loads(macdSell_data.to_json()) #macdSell_data_json['macdSell']    
    data_macdBuy[['macd', 'macdsignal', 'macdBuy', 'performance', 'performance_percent']] = data_macdBuy[['macd', 'macdsignal', 'macdBuy', 'performance', 'performance_percent']].applymap('{:,.2f}'.format)
    data_macdSell[['macd', 'macdsignal', 'macdSell', 'performance', 'performance_percent']] = data_macdSell[['macd', 'macdsignal', 'macdSell', 'performance', 'performance_percent']].applymap('{:,.2f}'.format)

    data_percentages = data[['Open', 'Close', 'High', 'Low']]
    data_percentages['rsi_percentage'] = data_rsi[['performance_percent']]
    data_percentages['macd_percentage'] = data_macdBuy[['performance_percent']]
    data_percentages['bbandle_percentage'] = data_bbandle[['performance_percent']]
    data_percentages['bbandse_percentage'] = data_bbandse[['performance_percent']]

    data_percentages['mean_buy_percentage'] = data_percentages['rsi_percentage'].apply(float) * 0.3 + data_percentages['macd_percentage'].apply(float) * 0.2 + data_percentages['bbandle_percentage'].apply(float) * 0.5
    data_percentages['mean_sell_percentage'] = data_percentages['rsi_percentage'].apply(float) * 0.3 + data_percentages['macd_percentage'].apply(float) * 0.2 + data_percentages['bbandse_percentage'].apply(float) * 0.5
    
    data_percentages['date'] = data.index.strftime('%b %d, %Y, %X')
    data[['Open', 'Close', 'High', 'Low']] = data[['Open', 'Close', 'High', 'Low']].applymap('{:,.2f}'.format)
    #data_percentages['macdSell_percentage'] = data_macdSell[['performance_percent']]

    pprint.pprint(data_percentages['mean_buy_percentage'])
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=(['','RSI','MACD']),  row_width=[0.2, 0.2, 0.7], vertical_spacing=0.1)
    fig.append_trace(go.Candlestick(x = data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color='#0384fc', decreasing_line_color='#e8482c',
                    text =  'Tarih: ' + data_percentages['date'].apply(str)  +
                            '<br><br>Açılış: ' + data_percentages['Open'].apply(str)  + 
                            '<br>Kapanış: ' + data_percentages['Close'].apply(str)  + 
                            '<br>En Yüksek: ' + data_percentages['High'].apply(str)  + 
                            '<br>En Düşük: ' + data_percentages['Low'].apply(str)  + 
                            '<br><br>RSI: ' + data_percentages['rsi_percentage'] + 
                            '%<br>MACD: ' + data_percentages['macd_percentage'] +
                            '%<br>BBand Al: ' + data_percentages['bbandle_percentage'] + 
                            '%<br>BBand Sat: ' + data_percentages['bbandse_percentage'] + 
                            '%<br><br>Ortalama Al: ' + data_percentages['mean_buy_percentage'].apply(str) +
                            '%<br>Ortalama Sat: ' + data_percentages['mean_sell_percentage'].apply(str),
                    hoverinfo = 'text',
                    name='Piyasa Verisi'), row=1, col=1)



    """fig.append_trace(go.Scatter(
            x=data.index,
            y=ema20,
            line=dict(color="#ff0000"),
            name="EMA 20"
        ), row=1, col=1)"""

    fig.append_trace(go.Scatter(
            x=data.index,
            y=ema50,
            line=dict(color="yellow"),
            hoverinfo='skip',
            name="EMA 50"
        ), row=1, col=1)

    """fig.append_trace(go.Scatter(
            x=data.index,
            y=ema100,
            line=dict(color="#00FFFF"),
            name="EMA 100"
        ), row=1, col=1)"""

    fig.append_trace(go.Scatter(
            x=data.index,
            y=ema200,
            line=dict(color="red"),
            hoverinfo='skip',
            name="EMA 200"
        ), row=1, col=1)

    golden_index = 0
    for key, value in goldenCross_data_json['goldenCross'].items():
        golden_index += 1
        golden_cross_ema50 = goldenCross_data_json['ema50'][key]
        golden_cross_ema200 = goldenCross_data_json['ema200'][key]
        fig.append_trace(go.Scatter(x=[key], y=[(golden_cross_ema50+golden_cross_ema200)/2],
                mode = 'markers',
                marker=dict(line=dict(color='yellow', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'yellow'),
                name = 'Golden Cross ' + str(golden_index)
                ), row=1, col=1)

    death_index = 0
    for key, value in deathCross_data_json['deathCross'].items():
        death_index += 1
        death_cross_ema50 = deathCross_data_json['ema50'][key]
        death_cross_ema200 = deathCross_data_json['ema200'][key]
        fig.append_trace(go.Scatter(x=[key], y=[(death_cross_ema50+death_cross_ema200)/2],
                mode = 'markers',
                marker=dict(line=dict(color='red', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'red'),
                name = 'Death Cross ' + str(death_index)
                ), row=1, col=1)

    fig.append_trace(go.Scatter(
            x=data.index,
            y=upperband,
            line=dict(color="#BB1587"),
            name="BBANDS Upperband",
            visible='legendonly'
        ), row=1, col=1)    
    
    fig.append_trace(go.Scatter(
            x=data.index,
            y=lowerband,
            line=dict(color="#BB1587"),
            name="BBANDS Lowerband",
            visible='legendonly'
        ), row=1, col=1)    
    
    fig.append_trace(go.Scatter(
            x=data.index,
            y=middleband,
            line=dict(color="#FAFAD2"),
            name="BBANDS Middleband",
            visible='legendonly'
        ), row=1, col=1)    

    fig.append_trace(go.Scatter(
            x=data.index,
            y=rsi,
            customdata=data_rsi[['performance_percent']],
            hovertemplate='%{customdata[0]}' + '%',
            line=dict(color="yellow"),
            name="RSI"
        ), row=2, col=1)

    fig.append_trace(go.Scatter(
            x=data.index,
            y=data['rsi_70'],
            hoverinfo='skip',
            showlegend = False,
            line=dict(color="white", dash='dash'),
            name="RSI Aşırı Alım"
        ), row=2, col=1)
    
    fig.append_trace(go.Scatter(
            x=data.index,
            y=data['rsi_30'],
            hoverinfo='skip',
            showlegend = False,
            line=dict(color="white", dash='dash'),
            name="RSI Aşırı Satım"
        ), row=2, col=1)

    rsiSell_index = 0
    for key, value in rsiSell_data_json['rsiSell'].items():
        rsiSell_index += 1
        rsiSell_value = rsiSell_data_json['rsi'][key]
        fig.append_trace(go.Scatter(x=[key], y=[rsiSell_value],
                mode = 'markers',
                showlegend = False,
                marker=dict(line=dict(color='red', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'red'),
                name = 'RSI Sat ' + str(rsiSell_index)
            ), row=2, col=1)

    rsiBuy_index = 0
    for key, value in rsiBuy_data_json['rsiBuy'].items():
        rsiBuy_index += 1
        rsiBuy_value = rsiBuy_data_json['rsi'][key]
        fig.append_trace(go.Scatter(x=[key], y=[rsiBuy_value],
                mode = 'markers',
                showlegend = False,
                marker=dict(line=dict(color='green', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'green'),
                name = 'RSI Al ' + str(rsiBuy_index)
            ), row=2, col=1)

    colors = np.where(macdhist < 0, 'red', 'green')
    fig.append_trace(
        go.Bar(
            x=data.index,
            y=macdhist,
            hoverinfo='skip',
            showlegend=False,
            name='MACD Histogram',
            marker_color=colors,
        ), row=3, col=1)

    fig.append_trace(go.Scatter(
            x=data.index,
            y=macd,
            customdata=data_macdBuy[['performance_percent']],
            hovertemplate='%{customdata[0]}' + '%',
            line=dict(color="blue"),
            name="MACD"
        ), row=3, col=1)

    fig.append_trace(go.Scatter(
            x=data.index,
            y=macdsignal,
            hoverinfo='skip',
            showlegend=False,
            line=dict(color="red"),
            #hovertemplate=None,
            name="MACDSIGNAL"
        ), row=3, col=1)

    fig.append_trace(go.Scatter(
            x=data.index,
            y=data['macd_0'],
            hoverinfo='skip',
            showlegend = False,
            line=dict(color="white", dash='dash'),
            name="MACD Sıfır Noktası"
        ), row=3, col=1)
    
    macdSell_index = 0
    for key, value in macdSell_data_json['macdSell'].items():
        macdSell_index += 1
        macdSell_value = macdSell_data_json['macd'][key]
        fig.append_trace(go.Scatter(x=[key], y=[macdSell_value],
                mode = 'markers',
                showlegend = False,
                marker=dict(line=dict(color='red', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'red'),
                name = 'MACD Sell Signal ' + str(macdSell_index)
            ), row=3, col=1)

    macdBuy_index = 0
    for key, value in macdBuy_data_json['macdBuy'].items():
        macdBuy_index += 1
        macdBuy_value = macdBuy_data_json['macd'][key]
        fig.append_trace(go.Scatter(x=[key], y=[macdBuy_value],
                mode = 'markers',
                showlegend = False,
                marker=dict(line=dict(color='green', width = 3),
                            symbol = 'circle-open-dot',
                            size = 11,
                            color = 'green'),
                name = 'MACD Buy Signal ' + str(macdBuy_index)
            ), row=3, col=1)

    bbandle_index = 0
    for key, value in bbandle_data_json['Low'].items():
        bbandle_index += 1
        fig.append_trace(go.Scatter(    
            x=[key],
            y=[value],
            showlegend = False,
            hoverinfo='skip',
            mode="text",
            textfont=dict(
                size=30,
                color="green"
            ),
            name="BBandLE " + str(bbandle_index),
            text= '\u2B06', #'\U0000290A, \U00002191', #arrow up
            textposition="bottom center"
    ), row=1, col=1)
    
    #data_bbandse

    bbandse_index = 0
    for key, value in bbandse_data_json['High'].items():
        bbandse_index += 1
        fig.append_trace(go.Scatter(
            x=[key],
            y=[value],
            showlegend = False,
            hoverinfo='skip',
            mode="text",
            textfont=dict(
                size=30,
                color="red"
            ),
            name="BBandSE " + str(bbandse_index),
            text= '\u2B07', #'\U000025bc', #arrow down
            textposition="top center"
    ), row=1, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        title=symbol_USD,
        hovermode='x unified',
        xaxis=dict(
            autorange=True
        ),
        yaxis=dict(
            autorange=True
        ),
        #hovertemplate = None,
        #text = ['Custom text {}'.format(i + 1) for i in range(5)],
        #dragmode='drawopenpath',
        newshape_line_color='white',
        yaxis_title='Market Fiyatı (USD)',
        xaxis_title='Tarih',
        height=1000

    )
    fig.update_traces(xaxis="x1")

    fig.update_xaxes(
        rangeslider_visible=False,
        showspikes=True,
        spikesnap="cursor",
        spikemode="across+marker",
        spikedash="dash",
        rangeselector=dict(
            buttons=list([
                #dict(count=15, label="15m", step="minute", stepmode="backward"),
                #dict(count=30, label="30", step="minute", stepmode="backward"),
                #dict(count=45, label="45m", step="minute", stepmode="backward"),
                #dict(count=1, label="1h", step="hour", stepmode="todate"),
                #dict(count=6, label="6h", step="hour", stepmode="backward"),
                #dict(count=12, label="12h", step="hour", stepmode="backward"),
                #dict(count=1, label="1d", step="day", stepmode="backward"),
                #dict(count=3, label="3d", step="day", stepmode="backward"),
                #dict(count=7, label="1w", step="day", stepmode="backward"),
                #dict(count=1, label="1mo", step="month", stepmode="backward"),
                #dict(count=3, label="3mo", step="month", stepmode="backward"),
                #dict(count=6, label="6mo", step="month", stepmode="backward"),
                #dict(step="all")
            ])
        )
    )

    fig.update_yaxes(
        showspikes=True,
        spikesnap="cursor",
        spikemode="across+marker",
        spikedash="dash",
        hoverformat="osman osman"
    )
    
    plot_div = plot(fig, output_type='div', config={'modeBarButtonsToAdd':['drawline',
                                        'drawopenpath',
                                        'drawclosedpath',
                                        'drawcircle',
                                        'drawrect',
                                        'eraseshape'
                                       ]})

   #pprint.pprint(data)
    return render(request, "analysis.html", context={'plot_div': plot_div})
