import numpy as np
import talib as ta

import prediction

import ctypes  
import sys
import math



# 打印绿色文字
def print_red_color_text(text):
    # 句柄号 
    STD_OUTPUT_HANDLE= -11  
    # 句柄
    handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)  
    # 设置
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, 0x02 | 0x08) # 绿字(加亮)
    # 显示
    sys.stdout.write(str(text))
    sys.stdout.write('\n')
    # 复原
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, 0x01 | 0x02 | 0x04)  # 白字
    

# 构造特征，用于机器学习
def build_features(series):
    '''构造特征，用于机器学习'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    timeperiod = 5
    # 原始数据
    #series
    # 低阶数据
    mean = ta.MA(close, timeperiod=timeperiod, matype=0)
    #mean = np.nan_to_num(mean) #Nan转换为0
    std = ta.STDDEV(close, timeperiod=timeperiod, nbdev=1)
    
    # 高阶数据
    rel = close - mean
    
    diff_mean = np.diff(mean) # 注意：长度减1
    diff_std = np.diff(std)
    diff_rel = np.diff(rel)
    
    #trend = np.where(diff_mean > 0, 1, -1)
    trend = []
    for i in range(len(diff_mean)):
        if diff_mean[i] == 0:
            trend.append(trend[-1])
        else:
            trend.append([-1,1][diff_mean[i] > 0])

    ud = [0]*timeperiod # 向上数+向下数
    tf = [0]*timeperiod # 与前同数+与前反数
    qs = [0]*timeperiod # 与趋势同+与趋势反数
    for i in range(timeperiod+1, len(series)+1):
        ud.append(np.sum(series[-timeperiod+i:i]))
        tf.append(np.sum(series[-timeperiod+i:i]==series[-timeperiod+i-1:i-1]))
        qs.append(np.sum(series[-timeperiod+i:i]==trend[-timeperiod+i-1:i-1])) # 因为trend长度少1
        
    #print(len(series[1:]),len(trend),len(std[1:]),len(diff_mean),len(diff_std),len(diff_rel),len(ud[1:]),len(tf[1:]),len(qs[1:]))
    X_all = np.column_stack((series[1:],trend,rel[1:],std[1:],diff_mean,diff_std,diff_rel,ud[1:],tf[1:],qs[1:]))
    X_all = np.nan_to_num(X_all)
    X, y, x_last = X_all[:-1], series[2:], X_all[-1].reshape(1,-1)
    
    return X, y, x_last
    
    
# 生成每期（追号）投注金额列表
def get_touzhu_list(peilv, start_beishu, zhushu, shouyilv, n=10):
    '''根据毛赔率、起始每注倍数、购买注数、收益率生成每期（追号）投注金额列表'''
    assert(peilv - zhushu > shouyilv)
    
    touzhu_list = []
    bs = start_beishu
    
    for i in range(n):
        while True:
            total = sum(touzhu_list) + bs * zhushu
            current_win = peilv * bs - total
            
            if current_win /total < shouyilv:
                bs += 1
            else:
                break
            
        touzhu_list.append(bs * zhushu)
        
    return touzhu_list
    

odds = 1.97      # 赔率     1.97
start_beishu = 5 # 起始倍数 5
shouyilv = 0.1   # 收益率   10%
n = 15           # 期数     15
times = get_touzhu_list(peilv=odds, start_beishu=start_beishu, zhushu=1, shouyilv=shouyilv, n=n) #10%


show_period = 121 #显示期数


# 策略：布林通道宽度
def strategy_bandwidth(series, n=2):
    '''策略：布林通道宽度'''
    
    # 实时线
    close = np.cumsum(series).astype(float)
    # 布林线
    upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    # 通道宽度
    bandwidth = upperband - lowerband
    
    mean = np.nan_to_num(bandwidth).mean()
    
    res = []
    current_signal = 0  # 当前信号：无
    for i in range(n, len(series)+1):
        # 判断是否有信号，什么信号
        #if bandwidth[i-1] < bandwidth[i]: # 增：趋势区间
        if bandwidth[i-1] > mean: # 宽：趋势区间
            current_signal = series[i-1] # 与前一期相同 //与前一期（趋势）相同
        else:                   # 窄：震荡区间
            current_signal = -series[i-1] # 与前一期相反
        
        res.append(current_signal)
    
    return np.array(res), bandwidth
    
    
    
# 策略：KDJ红线
def strategy_kdj(series, n):
    '''策略：KDJ红线 0 <----> 100'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    res = []
    current_signal = 0 # 当前信号：无
    is_up = False
    for i in range(n, len(series)+1):
        # 判断是否有信号，什么信号
        if fastk[i-1] == 0:  # 上升趋势
            is_up = True
        elif fastk[i-1] == 100: # 下降趋势
            is_up = False
        
        current_signal = [-1,1][is_up]
        
        res.append(current_signal)
    
    return np.array(res), fastk, fastd


strate_funcs = {
    '通道宽度': strategy_bandwidth,
    'KDJ红线': strategy_kdj,
}

# 切换策略（双主）
def switch_strategy(series, strate_name1, strate_name2):
    signals1, *_ = strate_funcs[strate_name1](series, n=2)
    signals2, *_ = strate_funcs[strate_name2](series, n=2)
    
    res1 = series[-show_period:] == signals1[-show_period-1:-1] # 比较对错
    res2 = series[-show_period:] == signals2[-show_period-1:-1] # 比较对错
    
    r = [] # 记录连错数
    current_strategy = 1
    res = [res2, res1][current_strategy]
    error_periods = 0
    for i in range(len(res1)):
        error_periods += 1
        r.append(error_periods)
        
        if res[i]:
            error_periods = 0
        else:
            if error_periods == 6: # 这个策略已经连错3期
                current_strategy = [1, 0][current_strategy == 1]
                res = [res2, res1][current_strategy] #切换策略
                #error_periods = 0
    
    return r

# 切换策略（主从）
def switch_strategy2(series, strate_name1, strate_name2):
    signals1, *_ = strate_funcs[strate_name1](series, n=2)
    signals2, *_ = strate_funcs[strate_name2](series, n=2)
    
    marster_res = series[-show_period:] == signals1[-show_period-1:-1] # 比较对错
    slave_res = series[-show_period:] == signals2[-show_period-1:-1] # 比较对错
    
    r = [] # 记录连错数
    current_is_marster = True
    res = [marster_res, slave_res][current_is_marster]
    marster_error_periods = 0 #主
    slave_periods = 0 #从计数
    
    for i in range(len(slave_res)):
        
        error_periods += 1
        r.append(error_periods)
        
        if not current_is_marster:
            slave_periods += 1
            if slave_periods == 10:
                current_is_marster = True#切换
        
        if res[i]:
            error_periods = 0
        else:
            if error_periods == 6: # 这个策略已经连错3期
                current_is_marster = False #切换策略
        
    
    
    return r


# 使用策略
def use_strategy(series, strate_name, is_backtest=True):
    
    if is_backtest:
        signals, *res = strate_funcs[strate_name](series, n=2)
        
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        
        for i in range(n, len(series)):
            if signals[i] == 0:
                order.append(0)
                earn.append(0)
                continue
            
            # 下单
            order.append(times[error_periods])
            
            # 对奖
            if signals[i-n] == series[i]:
                error_periods = 0  # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.97
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, res
            
    else:
        signals, *_ = strate_funcs[strate_name](series, n=200)
        
        print('='*30)
        print(strate_name, end=' ')
        print_red_color_text(signals[-1])
        print('='*30)
        return current_signal



