import matplotlib.pyplot as plt
import pandas as pd
import sys
import matplotlib
import matplotlib.dates as md
import numpy as np

def read_simulated_quotes (file, BETWEEN_START, BETWEEN_END):
  df = pd.read_pickle(file, compression='bz2')
  df['Timestamp'] = df.index

  # Keep only the last bid and last ask event at each timestamp.
  df = df.drop_duplicates(subset=['Timestamp','EventType'], keep='last')

  df = df.between_time( BETWEEN_START, BETWEEN_END )

  del df['Timestamp']

  df_bid = df[df['EventType'] == 'BEST_BID'].copy()
  df_ask = df[df['EventType'] == 'BEST_ASK'].copy()

  if len(df) <= 0:
    print ("There appear to be no simulated quotes.")
    sys.exit()

  df_bid['BEST_BID'] = [b for s,b,bv in df_bid['Event'].str.split(',')]
  df_bid['BEST_BID_VOL'] = [bv for s,b,bv in df_bid['Event'].str.split(',')]
  df_ask['BEST_ASK'] = [a for s,a,av in df_ask['Event'].str.split(',')]
  df_ask['BEST_ASK_VOL'] = [av for s,a,av in df_ask['Event'].str.split(',')]

  df_bid['BEST_BID'] = df_bid['BEST_BID'].str.replace('$','').astype('float64')
  df_ask['BEST_ASK'] = df_ask['BEST_ASK'].str.replace('$','').astype('float64')

  df_bid['BEST_BID_VOL'] = df_bid['BEST_BID_VOL'].astype('float64')
  df_ask['BEST_ASK_VOL'] = df_ask['BEST_ASK_VOL'].astype('float64')

  df = df_bid.join(df_ask, how='outer', lsuffix='.bid', rsuffix='.ask')
  df['BEST_BID'] = df['BEST_BID'].ffill().bfill()
  df['BEST_ASK'] = df['BEST_ASK'].ffill().bfill()
  df['BEST_BID_VOL'] = df['BEST_BID_VOL'].ffill().bfill()
  df['BEST_ASK_VOL'] = df['BEST_ASK_VOL'].ffill().bfill()

  df['MIDPOINT'] = (df['BEST_BID'] + df['BEST_ASK']) / 2.0
  df['SPREAD'] = df['BEST_ASK'] - df['BEST_BID']

  return df

# Auto-detect terminal width.
pd.options.display.width = None
pd.options.display.max_rows = 1000
pd.options.display.max_colwidth = 200

BETWEEN_START = pd.to_datetime('09:30').time()
BETWEEN_END = pd.to_datetime('13:00:00').time()

# Linewidth for plots.
LW = 4
plt.rcParams.update({'font.size': 20, 'font.weight': 'bold'})


folders = [
            "SIMGAN_100_1000_30270",
            "SIMGAN_100_1000_30939",
            "SIMGAN_100_1000_468509",
            "SIMGAN_100_1000_763193"
          ]
fig, ax = plt.subplots(figsize=(12, 9), nrows=1, ncols=1)
legend_array = []

for folder in folders:

  array_of_series = []

  sim_file = "log/" + folder + "/EXCHANGE_AGENT.bz2"
  axes = [ax]

  print(sim_file)
  mid = read_simulated_quotes(sim_file, BETWEEN_START, BETWEEN_END )
  array_of_series.append(mid['MIDPOINT'])

  avg = np.mean(array_of_series)

  mid['MIDPOINT'].plot( grid=True, linewidth=LW, alpha=0.9, ax=axes[0])
  ax.set_title("Simulated mid prices", fontsize =20, fontweight = 'bold')
  ax.set_ylabel('Price (cents)', fontsize =20, fontweight = 'bold')
  axes[0].set_xlabel('Time', fontsize =20, fontweight = 'bold')

  ax = plt.gca()
  xfmt = md.DateFormatter( '%H:%M:%S' )
  ax.xaxis.set_major_formatter(xfmt)
  ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:.0f}'))
  ax.minorticks_on()

  nm = str.split(sim_file, '/')

legend_array = ["1","2","3","4"
               ]
axes[0].legend( legend_array, fontsize =15 ) #, loc = 'center left', bbox_to_anchor=(1, 0.5) )

plt.subplots_adjust( left = 0.15)
output = sys.argv[1]
plt.savefig(output+'.png')
print( output+".png", " saved")
