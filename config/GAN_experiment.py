from Kernel import Kernel
import datetime as dt
from agent.ExchangeAgent import ExchangeAgent
from agent.NoiseAgent import NoiseAgent
from agent.ValueAgent import ValueAgent
import os
from util.oracle.SparseMeanRevertingOracle import SparseMeanRevertingOracle
import pandas as pd
import numpy as np
from agent.market_makers.MarketMakerAgent import MarketMakerAgent


num_value = 100
num_noise = 1000

seed = int(np.random.uniform(0,1e6))

simulation_start_time = dt.datetime.now()
print("Simulation Start Time: {}".format(simulation_start_time))
print("Configuration seed: {}\n".format(seed))
########################################################################################################################
############################################### AGENTS CONFIG ##########################################################

# Historical date to simulate.
historical_date = "20190621"
mkt_open = pd.to_datetime( historical_date ) + pd.to_timedelta('09:30:00')
mkt_close = pd.to_datetime( historical_date ) + pd.to_timedelta('16:00:00')
agent_count, agents, agent_types = 0, [], []

symbol = "JPM"
starting_cash = 10000000  # Cash in this simulator is always in CENTS.
log_orders = True

log_dir = "SIMGAN_"+ str(num_value) + "_" + str(num_noise) + "_" + str(seed)

r_bar = 1e5
kappa = 1.67e-12
agent_kappa = 1.67e-15
sigma_s = 0
fund_vol = 1e-4
megashock_lambda_a = 2.77778e-13
megashock_mean = 1e3
megashock_var = 5e4
symbols = {
symbol: {
    'r_bar' : r_bar,
    'kappa' : kappa,
    'agent_kappa' : agent_kappa,
    'sigma_s' : sigma_s,
    'fund_vol' : fund_vol,
    'megashock_lambda_a' : megashock_lambda_a ,
    'megashock_mean' : megashock_mean,
    'megashock_var' : megashock_var,
    'random_state': np.random.RandomState(seed=np.random.randint(low=0, high=2 ** 32, dtype='uint64'))
}
}
oracle = SparseMeanRevertingOracle(mkt_open, mkt_close, symbols)

path = os.path.join(".", "log", log_dir)
if not os.path.exists(path):
    # 1) Exchange Agent
    agents.extend([ExchangeAgent(id=0,
                                 name="EXCHANGE_AGENT",
                                 type="ExchangeAgent",
                                 mkt_open=mkt_open,
                                 mkt_close=mkt_close,
                                 symbols=[symbol],
                                 log_orders=log_orders,
                                 pipeline_delay=0,
                                 computation_delay=0,
                                 stream_history=10,
                                 book_freq=0,
                                 random_state=np.random.RandomState(
                                     seed=np.random.randint(low=0, high=2 ** 32, dtype='uint64')))])
    agent_types.extend("ExchangeAgent")
    agent_count += 1

    # 2) Noise Agents
    agents.extend([NoiseAgent(j, "NoiseAgent {}".format(j),
                              "NoiseAgent",
                              random_state=np.random.RandomState(
                                  seed=np.random.randint(low=0, high=2 ** 32, dtype='uint64')),
                              log_orders=log_orders, symbol=symbol, starting_cash=starting_cash,
                              wakeup_time=mkt_open + np.random.rand() * (mkt_close - mkt_open)) for j in
                   range(agent_count, agent_count + num_noise )])
    agent_count += num_noise
    agent_types.extend(['NoiseAgent' for j in range(num_noise)])

    # 3) Value Agents
    agents.extend([ValueAgent(j, "ValueAgent {}".format(j),
                              "ValueAgent {}".format(j),
                              random_state=np.random.RandomState(
                                  seed=np.random.randint(low=0, high=2 ** 32, dtype='uint64')),
                              r_bar=r_bar, lambda_a=1e-13, sigma_n=r_bar/10, kappa=kappa,
                              log_orders=log_orders, symbol=symbol) for j in
                   range(agent_count, agent_count + num_value)])
    agent_types.extend(["ValueAgent {}".format(j) for j in range(num_value)])
    agent_count += num_value

    #4) Market Maker Agent
    num_mm_agents = 1
    agents.extend([MarketMakerAgent(id=j,
                                    name="MarketMakerAgent {}".format(j),
                                    type='MarketMakerAgent',
                                    symbol=symbol,
                                    starting_cash=starting_cash,
                                    min_size = 50,
                                    max_size = 150,
                                    wake_up_freq="1min",
                                    log_orders=False,
                                    subscribe=False,
                                    random_state=np.random.RandomState(seed=np.random.randint(low=0, high=2 ** 32,
                                                                                              dtype='uint64')),
                                    #spread=2,
                                    #depth=10,
                                    )
                   for j in range(agent_count, agent_count + num_mm_agents)])
    agent_types.extend(["MarketMakerAgent {}".format(j) for j in range(num_mm_agents)])
    agent_count += num_mm_agents

    kernel = Kernel("Kernel",
                    random_state=np.random.RandomState(seed=np.random.randint(low=0, high=2 ** 32,
                                                                          dtype='uint64')))
    kernelStartTime = mkt_open
    kernelStopTime = pd.to_datetime(historical_date) + pd.to_timedelta('16:01:00')

    defaultComputationDelay = 0
    latency = np.zeros((agent_count, agent_count))
    noise = [0.0]

    kernel.runner(agents=agents,
                  startTime=kernelStartTime,
                  stopTime=kernelStopTime,
                  agentLatency=latency,
                  latencyNoise=noise,
                  defaultComputationDelay=defaultComputationDelay,
                  defaultLatency=0,
                  oracle=oracle,
                  log_dir=log_dir)

simulation_end_time = dt.datetime.now()
print("Simulation End Time: {}".format(simulation_end_time))
print("Time taken to run simulation: {}".format(simulation_end_time - simulation_start_time))
