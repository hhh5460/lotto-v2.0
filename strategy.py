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
n = 20           # 期数     15
times = get_touzhu_list(peilv=odds, start_beishu=start_beishu, zhushu=1, shouyilv=shouyilv, n=n) #10%


show_period = 121 #显示期数




# 策略：布林通道宽度
def strategy_bandwidth(series, is_backtest=True):
    '''策略：布林通道宽度'''
    
    # 实时线
    close = np.cumsum(series).astype(float)
    # 布林线
    upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    
    bandwidth = upperband - lowerband
    bandwidth_mean = np.nan_to_num(bandwidth).mean()
    
    current_signal = 0  # 当前信号：无
    
    # 计算趋势
    mean = ta.MA(close, timeperiod=5, matype=0)
    #mean = np.nan_to_num(mean) #Nan转换为0
    diff_mean = np.diff(mean) # 注意：长度减1
    
    #trend = np.where(diff_mean > 0, 1, -1)
    trend = []
    for i in range(len(diff_mean)):
        if diff_mean[i] == 0:
            trend.append(trend[-1])
        else:
            trend.append([-1,1][diff_mean[i] > 0])
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = []           # 收益记录
        order = []          # 投注资金记录
        
        for i in range(2, len(series)):
            
            # 判断是否有信号，什么信号
            #if bandwidth[i-1] < bandwidth[i]: # 增：趋势区间
            if bandwidth[i-1] > bandwidth_mean: # 宽：趋势区间
                #current_signal = series[-1] # 与前一期相同
                current_signal = trend[i-2] # 与前一期趋势相同
            else:                   # 窄：震荡区间
                current_signal = -series[i-1] # 与前一期相反（注意不一样！！）
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, bandwidth, bandwidth_mean
    # 否则只显示最后一期
    else:
        # 应肖的需求，显示下期结果
        if bandwidth[-1] > mean: # 宽：趋势区间
            current_signal = trend[-1] # 与前一期（趋势）相同
        else:                   # 窄：震荡区间
            current_signal = -series[-1] # 与前一期相反
        print('='*30)
        print('通道宽度： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal
    

# 策略：绝对金叉死叉（注意：已修改，其实不能再叫金叉死叉了！！）
def strategy_gold_die(series, is_backtest=True):
    '''策略：绝对金叉死叉'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 快慢均线
    ma_fast = ta.MA(close, timeperiod=6, matype=0)
    ma_slow = ta.MA(close, timeperiod=12, matype=0)
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        is_gold = False
        
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            y1, y2 = ma_fast[i-2], ma_fast[i-1]
            y3, y4 = ma_slow[i-2], ma_slow[i-1]
            
            if y1 - y3 < 0 and y2 - y4 >= 0:   # 金叉瞬间
                is_gold = True
            elif y1 - y3 > 0 and y2 - y4 <= 0: # 死叉瞬间
                is_gold = False

            if is_gold and (y1 > y2 and y3 >= y4): # 假金叉
                current_signal = -1
            elif not is_gold and (y1 < y2 and y3 <= y4): # 假死叉
                current_signal = 1
            else:
                current_signal = [-1, 1][is_gold]
                
            #if y1 - y3 < y2 - y4:   # 上升
            #    current_signal = 1
            #elif y1 - y3 > y2 - y4: # 下降
            #    current_signal = -1
            #else:
            #    pass
            
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, ma_fast, ma_slow
    else:
        y1, y2 = ma_fast[-2], ma_fast[-1]
        y3, y4 = ma_slow[-2], ma_slow[-1]
        if y1 - y3 < 0 and y2 - y4 > 0:   # 金叉
            current_signal = 1
        elif y1 - y3 > 0 and y2 - y4 < 0: # 死叉
            current_signal = -1
        else:
            pass
            
        #if y1 - y3 < y2 - y4:   # 上升
        #    current_signal = 1
        #elif y1 - y3 > y2 - y4: # 下降
        #    current_signal = -1
        #else:
        #    pass
        print('='*30)
        print('金叉死叉： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        return current_signal

# 策略：均线差分
def strategy_mean_diff(series, is_backtest=True):
    '''策略：快慢均线差分'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 快慢均线
    ma_fast = ta.MA(close, timeperiod=6, matype=0)
    ma_slow = ta.MA(close, timeperiod=15, matype=0)
    # 均线差分
    sub_mean_diff = np.diff(ma_fast - ma_slow) # 长度减1
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        
        #for i in range(2, len(series)):
            # 判断是否有信号，什么信号
        #    if sub_mean_diff[i-1] > 0:   # 距离增大
        for i in range(102, len(series)):
            # 判断是否有信号，什么信号
            #if sub_mean_diff[i-2] > 0:   # 距离增大
            #    if ma_slow[i-2] < ma_slow[i-1]:
            #        current_signal = np.random.choice([-1, 1], 1, p=[0.25, 0.75])[0]
            #    else:
            #        current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
            #else: # 距离减小
            #    if ma_slow[i-2] > ma_slow[i-1]:
            #        current_signal = np.random.choice([-1, 1], 1, p=[0.75, 0.25])[0]
            #    else:
            #        current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
                    
            if sub_mean_diff[i-2] > 0:   # 距离增大
                a = sub_mean_diff[i-102:i-2]
                pre_avg = np.where(a>0, a, 0).sum() / np.where(a>0, 1, 0).sum() # 大于0的均值
                if sub_mean_diff[i-2] > pre_avg:
                    current_signal = np.random.choice([-1, 1], 1, p=[0.1, 0.9])[0]
                else:
                    current_signal = np.random.choice([-1, 1], 1, p=[0.3, 0.7])[0]
            else: # 距离减小
                a = sub_mean_diff[i-102:i-2]
                pre_avg = np.where(a<0, a, 0).sum() / np.where(a<0, 1, 0).sum() # 小于0的均值
                if sub_mean_diff[-1] < pre_avg:
                    current_signal = np.random.choice([-1, 1], 1, p=[0.9, 0.1])[0]
                else:
                    current_signal = np.random.choice([-1, 1], 1, p=[0.7, 0.3])[0]
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, ma_fast, ma_slow
    else:
        #if sub_mean_diff[-1] > 0:   # 距离增大
        #    if ma_slow[-2] < ma_slow[-1]:
        #        current_signal = np.random.choice([-1, 1], 1, p=[0.25, 0.75])[0]
        #    else:
        #        current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
        #else: # 距离减小
        #    if ma_slow[-2] > ma_slow[-1]:
        #        current_signal = np.random.choice([-1, 1], 1, p=[0.75, 0.25])[0]
        #    else:
        #        current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
                
        if sub_mean_diff[-1] > 0:   # 距离增大
            a = sub_mean_diff[-100:]
            pre_avg = np.where(a>0, a, 0).sum() / np.where(a>0, 1, 0).sum() # 大于0的均值
            if sub_mean_diff[-1] > pre_avg:
                current_signal = np.random.choice([-1, 1], 1, p=[0.1, 0.9])[0]
            else:
                current_signal = np.random.choice([-1, 1], 1, p=[0.3, 0.7])[0]
        else: # 距离减小
            a = sub_mean_diff[-100:]
            pre_avg = np.where(a<0, a, 0).sum() / np.where(a<0, 1, 0).sum() # 小于0的均值
            if sub_mean_diff[-1] < pre_avg:
                current_signal = np.random.choice([-1, 1], 1, p=[0.9, 0.1])[0]
            else:
                current_signal = np.random.choice([-1, 1], 1, p=[0.7, 0.3])[0]
        print('='*30)
        print('均线差分： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        return current_signal


# 策略：顺势而为
def strategy_ma(series, is_backtest=True):
    '''策略：顺势'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 均线
    ma = ta.MA(close, timeperiod=10, matype=0)
    ma = np.nan_to_num(ma) #Nan转换为0
    
    #ma_fast = ta.MA(close, timeperiod=5, matype=0)
    #ma_fast = np.nan_to_num(ma) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            if ma[i-2] < ma[i-1]:  # 上升趋势
                current_signal = 1
            elif ma[i-2] > ma[i-1]: # 下降趋势
                current_signal = -1
            else:
                #current_signal = [-1, 1][ma_fast[i-2] < ma_fast[i-1]]
                #current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
                current_signal = 1 * series[i-1]
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        return order, earn, ma
    else:
        if ma[-2] < ma[-1]:  # 上升趋势
            current_signal = 1
        elif ma[-2] > ma[-1]: # 下降趋势
            current_signal = -1
        else:
            #current_signal = [-1, 1][ma_fast[-2] < ma_fast[-1]]
            #current_signal = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[0]
            current_signal = -1 * series[-1]
        print('='*30)
        print('顺势而为： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal
    
    
# 策略：KDJ红线
def strategy_kdj_(series, is_backtest=True):
    '''策略：KDJ红线 0 <----> 100'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        is_up = False
        
        for i in range(1, len(series)):
            # 判断是否有信号，什么信号
            if fastk[i-1] == 0:  # 上升趋势
                is_up = True
            elif fastk[i-1] == 100: # 下降趋势
                is_up = False
            
            current_signal = [-1,1][is_up]
            
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, fastk, fastd
    else:
        if fastk[-1] == 0:  # 上升趋势
            current_signal = 1
        elif fastk[-1] == 100: # 下降趋势
            current_signal = -1
        else:
            pass
        print('='*30)
        print('KDJ转换： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal

# 策略：KDJ绿线
def strategy_kdj(series, is_backtest=True):
    '''策略：KDJ绿线'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        is_up = False
        
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            #y1, y2 = fastk[i-2], fastk[i-1] # 红线
            y3, y4 = fastd[i-2], fastd[i-1] # 绿线
            
            
            if y4 > 85:   # 绿线85+
                current_signal = 1
                #is_up = False
            elif y4 < 15:    # 绿线15-
                current_signal = -1
                #is_up = True
            elif abs(y4 - y3) < 0.01: # 绿线水平
            #if abs(y4 - y3) < math.tan(math.pi/12): # 正负15度之间
                current_signal = series[i-1] # 与上期同！！！
            else:
                current_signal = [-1, 1][y4 - y3 > 0] # 与绿线同向
            
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, fastk, fastd
    else:
        if fastk[-1] == 0:  # 上升趋势
            current_signal = 1
        elif fastk[-1] == 100: # 下降趋势
            current_signal = -1
        else:
            pass
        print('='*30)
        print('KDJ转换： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal


# 策略：KDJ红绿
def strategy_kdj2(series, is_backtest=True):
    '''策略：KDJ红绿'''
    
    
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        is_up = False
        
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            y1, y2 = fastk[i-2], fastk[i-1] # 红线
            y3, y4 = fastd[i-2], fastd[i-1] # 绿线
            
            if y2 < 0.5:      # 红线触底
                is_up = True
            elif y2 > 99.5:  # 红线触顶
                is_up = False
            
            if abs(y4 - y3) < 0.9: # 绿线水平
            #if abs(y4 - y3) < math.tan(math.pi/12): # 正负15度之间
                current_signal = series[i-1] # 与上期同！！！
            elif y4 > 95:   # 绿线触顶
                current_signal = 1
            elif y4 < 5:    # 绿线触底
                current_signal = -1
            else:
                current_signal = [-1, 1][is_up]
                
            
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, fastk, fastd
    else:
        is_up = False
        
        for i in range(300, len(series)+1):
            # 判断是否有信号，什么信号
            y1, y2 = fastk[i-2], fastk[i-1] # 红线
            y3, y4 = fastd[i-2], fastd[i-1] # 绿线
            
            if y2 < 0.5:      # 红线触底
                is_up = True
            elif y2 > 99.5:  # 红线触顶
                is_up = False
                
            if abs(y4 - y3) < 0.01: # 如果绿线水平
                current_signal = series[i-1] # 与上期同！！！
            elif y4 > 95:   # 绿线触顶
                current_signal = 1
            elif y4 < 5:    # 绿线触底
                current_signal = -1
            else:
                current_signal = [-1, 1][is_up]
        print('='*30)
        print('KDJ绿线： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
    
        return current_signal


# 策略：KDJ稻草(肖氏理论之救命稻草)
def strategy_kdj2__(series, is_backtest=True):
    '''策略：KDJ 0 <----> 100'''
    
    
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            if fastd[i-1] <= 25:  # 绿线[0,25]
                current_signal = -1
            elif fastd[i-1] >= 75: # 绿线[75,100]
                current_signal = 1
            else:
                #if fastd[i-1] - fastd[i-2] > 0: # 以绿线为准
                #if fastk[i-1] - fastk[i-2] > 0: # 以红线为准
                #if fastk[i-1] > fastd[i-1]: # 红线在上
                #    current_signal = 1
                #else:
                #    current_signal = -1
                if (fastk[i-2] - fastd[i-2]) * (fastk[i-1] - fastd[i-1]) < 0: # 相交，则
                    current_signal = [-1, 1][fastd[i-1] - fastd[i-2] > 0]     # 以绿线为准
                elif fastk[i-1] - fastk[i-2] == 0:              # 水平，则
                    current_signal = [-1, 1][fastk[i-1] > 50]   # 大于50，向上；小于50，向下
                elif fastd[i-1] - fastd[i-2] == 0:
                    current_signal = [-1, 1][fastd[i-1] > 50]
                else:                                                     # 无相交，则
                    current_signal = [-1, 1][fastk[i-1] - fastk[i-2] > 0] # 以红线为准
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, fastk, fastd
    else:
        if fastd[-1] <= 25:  # 绿线[0,25]
            current_signal = -1
        elif fastd[-1] >= 75: # 绿线[75,100]
            current_signal = 1
        else:
            #if fastd[-1] - fastd[-2] > 0: # 以绿线为准
            #if fastk[-1] - fastk[-2] > 0: # 以红线为准
            #if fastk[-1] > fastd[-1]: # 红线在上
            #    current_signal = 1
            #else:
            #    current_signal = -1
            if (fastk[-2] - fastd[-2]) * (fastk[-1] - fastd[-1]) < 0: # 相交，则
                current_signal = [-1, 1][fastd[-1] - fastd[-2] > 0]     # 以绿线为准
            elif fastk[-1] - fastk[-2] == 0:              # 水平，则
                current_signal = [-1, 1][fastk[-1] > 50]   # 大于50，向上；小于50，向下
            elif fastd[-1] - fastd[-2] == 0:
                current_signal = [-1, 1][fastd[-1] > 50]
            else:                                                     # 无相交，则
                current_signal = [-1, 1][fastk[-1] - fastk[-2] > 0] # 以红线为准
            
        print('='*30)
        print('KDJ绿线： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
    
        return current_signal

# 策略：KDJ肖氏(肖氏理论之理论突破)
def strategy_kdj3(series, is_backtest=True):
    '''策略：KDJ 0 <----> 100'''
    
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # KDJ
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    #fastk = np.nan_to_num(fastk) #Nan转换为0

    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            if (fastk[i-1] - fastk[i-2]) > 0 and (fastd[i-1] - fastd[i-2]) > 0: # 红、绿同上
                current_signal = 1
            if (fastk[i-1] - fastk[i-2]) < 0 and (fastd[i-1] - fastd[i-2]) < 0: # 红、绿同下
                current_signal = -1
            elif (fastk[i-2] - fastd[i-2]) * (fastk[i-1] - fastd[i-1]) == 0:    # 红、绿之一水平
                current_signal = series[i-1]
            else:
                current_signal = [-1, 1][fastd[i-1] >= 50]   # 绿线50+，向上；绿线50-，向下

                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, fastk, fastd
    else:
        if (fastk[-1] - fastk[-2]) > 0 and (fastd[-1] - fastd[-2]) > 0: # 红、绿同上
            current_signal = 1
        if (fastk[-1] - fastk[-2]) < 0 and (fastd[-1] - fastd[-2]) < 0: # 红、绿同下
            current_signal = -1
        elif (fastk[-2] - fastd[-2]) * (fastk[-1] - fastd[-1]) == 0:    # 红、绿之一水平
            current_signal = series[-1]
        else:
            current_signal = [-1, 1][fastd[-1] >= 50]   # 绿线50+，向上；绿线50-，向下
            
        print('='*30)
        print('KDJ肖氏： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
    
        return current_signal



# 策略：随机漫步
def strategy_rnd(series, is_backtest=True):
    '''策略：随机漫步'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 随机
    rnd = []
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        for i in range(1, len(series)):
            
            # 随机信号
            rnd.append(np.random.choice([-1, 1]))
            current_signal = rnd[-1]
            
            
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))

        return order, earn, rnd
    else:
        current_signal = np.random.choice([-1, 1])
        print('='*30)
        print('随机漫步： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal
        

# 策略：希尔伯特正弦变换
def strategy_ht_sine(series, is_backtest=True):
    '''策略：希尔伯特正弦变换'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 希尔伯特正弦变换
    sine, leadsine = ta.HT_SINE(close)
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        
        for i in range(2, len(series)):
            # 判断是否有信号，什么信号
            y1, y2 = sine[i-2], sine[i-1]
            y3, y4 = leadsine[i-2], leadsine[i-1]
            if y1 > y3 and y2 < y4:
                current_signal = -1
            elif y1 < y3 and y2 > y4:
                current_signal = 1
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))

        return order, earn, sine, leadsine
    else:
        y1, y2 = sine[-2], sine[-1]
        y3, y4 = leadsine[-2], leadsine[-1]
        if y1 > y3 and y2 < y4:
            current_signal = -1
        elif y1 < y3 and y2 > y4:
            current_signal = 1
        print('='*30)
        print('正弦变换： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal

# 策略：希尔伯特正弦变换2
def strategy_ht_sine2(series, is_backtest=True):
    '''策略：希尔伯特正弦变换'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 希尔伯特正弦变换
    sine, leadsine = ta.HT_SINE(close)
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        
        for i in range(1, len(series)):
            # 判断是否有信号，什么信号
            if sine[i-1] > leadsine[i-1]: # 红线在上
                current_signal = 1
            else:
                current_signal = 1
                
            # 若无信号，跳过，不做任何操作
            #if current_signal == 0: continue
            
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))

        return order, earn, sine, leadsine
    else:
        if sine[-1] < leadsine[-1]: # 红线在下
            current_signal = -1
        else:
            current_signal = 1
        print('='*30)
        print('正弦变换： ',end='')
        print_red_color_text(current_signal)
        print('='*30)
        
        return current_signal


# 策略：机器学习
def strategy_ml(series, ml_name, is_backtest=True):
    '''策略：机器学习'''
    X, y, x_last = build_features(series)

    #clf_names = ['AdaBoost', 'Bagging', 'ExtraTrees', 'GradientBoost', 'RandomForest', 'Voting', 'bayies', 'KNeighbors', 'svc', 'DecisionTree', 'ExtraTree', 'sk_nn', 'feature_selection1', 'feature_selection2', 'GridSearch', 'RandomizedSearch', 'nn']

    ml = []
    
    current_signal = 0 # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        error_periods = 0 # 哨兵：之前错误期数
        earn = [] # 收益记录
        order = [] # 投注资金记录
        
        for i in range(200, len(X)):
            # 判断是否有信号，什么信号
            if ml_name == 'ALL':
                #clf_names = ['AdaBoost', 'Bagging', 'ExtraTrees', 'GradientBoost', 'RandomForest', 'Voting', 'bayies', 'KNeighbors', 'svc', 'DecisionTree', 'ExtraTree', 'sk_nn', 'feature_selection1', 'feature_selection2', 'GridSearch', 'RandomizedSearch', 'nn']
                clf_names = ['Bagging', 'ExtraTrees', 'GradientBoost', 
                            'RandomForest', 'Voting', 'bayies', 'KNeighbors', 
                            'svc', 'DecisionTree', 'ExtraTree', 'feature_selection1'] # 11个

                pred_res = []
                for clf_name in clf_names:
                    clf = prediction.classifiers[clf_name]
                    clf.fit(X[-100+i:i, :], y[-100+i:i]) # 用[0,1,...,99]来训练
                    y0 = clf.predict(X[i, :].reshape(1,-1))[0] # 预测
                    pred_res.append(y0)
                up = pred_res.count(1)
                down = pred_res.count(-1)
                tol = up - down
                current_signal =[-1,1][tol>0]
                #current_signal = 1 if tol > 0 else -1
            else:
                clf = prediction.classifiers[ml_name] # AdaBoost
                clf.fit(X[-100+i:i, :], y[-100+i:i]) # 用[0,1,...,99]来训练
                current_signal = clf.predict(X[i, :].reshape(1,-1))[0] # 预测
            
            
            ml.append(current_signal)
                
            # 若无信号，跳过，不做任何操作
            if current_signal == 0: 
                order.append(0)
                earn.append(0)
                continue
            
            # 看料
            buy = current_signal
            
            # 下单
            order.append(times[error_periods])
            
            
            # 判断对错，计算收益
            if buy == series[i+2]:
                error_periods = 0 # 错误期数置零
                earn.append(odds * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1 # 错误期数加一
                earn.append(0)
                
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, ml
    else:
        if ml_name == 'ALL':
            clf_names = ['Bagging', 'ExtraTrees', 'GradientBoost', 
                         'RandomForest', 'Voting', 'bayies', 'KNeighbors', 
                         'svc', 'DecisionTree', 'ExtraTree', 'feature_selection1'] # 11个
            pred_res = []
            for clf_name in clf_names:
                clf = prediction.classifiers[clf_name]
                clf.fit(X[-100:, :], y[-100:]) # 用[-100,-99,...,-1]来训练
                y0 = clf.predict(x_last)[0] # 预测
                pred_res.append(y0)
            up = pred_res.count(1)
            down = pred_res.count(-1)
            tol = up - down
            
            last_signal = 1 if tol > 0 else -1
        else:
            clf = prediction.classifiers[ml_name] # AdaBoost
            clf.fit(X[-100:, :], y[-100:]) # 用[-100,-99,...,-1]来训练
            last_signal = clf.predict(x_last)[0] # 预测

        print('='*30)
        print('机器学习({})： '.format(ml_name),end='')
        print_red_color_text(last_signal)
        print('='*30)
        
        return last_signal


# 策略：三种综合
def strategy_three(series, is_backtest=True):
    '''策略：布林通道宽度、顺势而为、KDJ极限'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 布林通道宽度
    upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    bandwidth = upperband - lowerband
    mean = np.nan_to_num(bandwidth).mean()
    
    # 顺势而为
    ma = ta.MA(close, timeperiod=10, matype=0)
    ma = np.nan_to_num(ma) #Nan转换为0
    
    # KDJ极限
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    
    signals = []
    current_signal = [0] * 3  # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        pre_is_right = True # 哨兵：上期投注正确
        earn = []           # 收益记录
        order = []          # 投注资金记录
        
        for i in range(2, len(series)):
            
            # 布林通道宽度
            #if bandwidth[i-1] < bandwidth[i]: # 增：趋势区间
            if bandwidth[i-1] > mean: # 宽：趋势区间
                current_signal[0] = series[i-1] # 与前一期相同 //与前一期（趋势）相同
            else:                   # 窄：震荡区间
                current_signal[0] = -series[i-1] # 与前一期相反
                
                
            # 顺势而为
            if ma[i-2] < ma[i-1]:  # 上升趋势
                current_signal[1] = 1
            else:               # 下降趋势
                current_signal[1] = -1
                
            # KDJ极限
            if fastk[i-1] == 0:  # 上升趋势
                current_signal[2] = 1
            elif fastk[i-1] == 100: # 下降趋势
                current_signal[2] = -1
            
                
            # 若无信号，跳过，不做任何操作
            if sum(current_signal) == 0: continue
            
            # 看料
            buy = [-1, 1][sum(current_signal)>0]
            
            
            if i < len(series)-1: # 若不是最后一期，则
                signals.append(buy)
                
                # 下单
                order.append(times[error_periods])
                
                
                # 判断对错，计算收益
                if buy == series[i]:
                    error_periods = 0 # 错误期数置零
                    earn.append(odds * order[-1]) # 赔率odds=1.96 
                else:
                    error_periods += 1 # 错误期数加一
                    earn.append(0)
            else:
                print(buy)

        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))

        return order, earn, signals
    else:
        # 布林通道宽度
        if bandwidth[-1] > mean: # 宽：趋势区间
            current_signal[0] = series[-1] # 与前一期相同 //与前一期（趋势）相同
        else:                   # 窄：震荡区间
            current_signal[0] = -series[-1] # 与前一期相反
        
        # 顺势而为
        if ma[-2] < ma[-1]:  # 上升趋势
            current_signal[1] = 1
        else:               # 下降趋势
            current_signal[1] = -1
            
        # KDJ极限
        if fastk[-1] == 0:  # 上升趋势
            current_signal[2] = 1
        elif fastk[-1] == 100: # 下降趋势
            current_signal[2] = -1

        
        print('='*30)
        print('三种综合： ',end='')
        print_red_color_text([-1, 1][sum(current_signal)>0])
        print('='*30)
        
        return [-1, 1][sum(current_signal)>0]
        
    
    
# 策略：五种综合
def strategy_five(series, is_backtest=True):
    '''策略：布林通道宽度、金叉死叉、顺势而为、KDJ零百转换、随机漫步'''
    # 实时线
    close = np.cumsum(series).astype(float)
    
    # 布林通道宽度
    upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    bandwidth = upperband - lowerband
    mean = np.nan_to_num(bandwidth).mean()
    
    # 金叉死叉
    ma_fast = ta.MA(close, timeperiod=8, matype=0)
    ma_slow = ta.MA(close, timeperiod=20, matype=0)
    
    # 顺势而为
    ma = ta.MA(close, timeperiod=10, matype=0)
    ma = np.nan_to_num(ma) #Nan转换为0
    
    # KDJ极限
    fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    
    # 随机漫步
    rnd = []
    
    signals = []
    current_signal = [0] * 5  # 当前信号：无
    
    # 如果是回测
    if is_backtest:
        pre_is_right = True # 哨兵：上期投注正确
        earn = []           # 收益记录
        order = []          # 投注资金记录
        
        for i in range(2, len(series)):
            
            # 布林通道宽度
            #if bandwidth[i-1] < bandwidth[i]: # 增：趋势区间
            if bandwidth[i-1] > mean: # 宽：趋势区间
                current_signal[0] = series[i-1] # 与前一期相同 //与前一期（趋势）相同
            else:                   # 窄：震荡区间
                current_signal[0] = -series[i-1] # 与前一期相反
                
            # 金叉死叉
            y1, y2 = ma_fast[i-2], ma_fast[i-1]
            y3, y4 = ma_slow[i-2], ma_slow[i-1]
            if y1 < y3 and y2 > y4:   # 金叉
                current_signal[1] = 1
            elif y1 > y3 and y2 < y4: # 死叉
                current_signal[1] = -1
                
            # 顺势而为
            if ma[i-2] < ma[i-1]:  # 上升趋势
                current_signal[2] = 1
            else:               # 下降趋势
                current_signal[2] = -1
                
            # KDJ极限
            if fastk[i-1] == 0:  # 上升趋势
                current_signal[3] = 1
            elif fastk[i] == 100: # 下降趋势
                current_signal[3] = -1
            
            # 随机漫步
            rnd.append(np.random.choice([-1, 1]))
            current_signal[4] = rnd[-1]
            
            # 若无信号，跳过，不做任何操作
            if sum(current_signal) == 0: continue
            
            # 看料
            buy = [-1, 1][sum(current_signal)>0]
            
            if i < len(series)-1: # 若不是最后一期，则
                signals.append(buy)
            
                # 下单
                order.append(times[error_periods])
                
                
                # 判断对错，计算收益
                if buy == series[i]:
                    error_periods = 0 # 错误期数置零
                    earn.append(odds * order[-1]) # 赔率odds=1.96 
                else:
                    error_periods += 1 # 错误期数加一
                    earn.append(0)
            else:
                print(buy)
        
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        return order, earn, signals
    else:
        # 布林通道宽度
        if bandwidth[-1] > mean: # 宽：趋势区间
            current_signal[0] = series[-1] # 与前一期相同 //与前一期（趋势）相同
        else:                   # 窄：震荡区间
            current_signal[0] = -series[-1] # 与前一期相反
        
        # 金叉死叉
        y1, y2 = ma_fast[-2], ma_fast[-1]
        y3, y4 = ma_slow[-2], ma_slow[-1]
        if y1 < y3 and y2 > y4:   # 金叉
            current_signal[1] = 1
        elif y1 > y3 and y2 < y4: # 死叉
            current_signal[1] = -1
            
        # 顺势而为
        if ma[-2] < ma[-1]:  # 上升趋势
            current_signal[2] = 1
        else:               # 下降趋势
            current_signal[2] = -1
            
        # KDJ极限
        if fastk[-1] == 0:  # 上升趋势
            current_signal[3] = 1
        elif fastk[-1] == 100: # 下降趋势
            current_signal[3] = -1

        # 随机漫步
        current_signal[4] = np.random.choice([-1, 1])
        
        print('='*30)
        print('五种综合： ',end='')
        print_red_color_text([-1, 1][sum(current_signal)>0])
        print('='*30)
        
        return [-1, 1][sum(current_signal)>0]

strategies = {
    '金叉死叉': strategy_gold_die,
    '均线差分': strategy_mean_diff,
    '通道宽度': strategy_bandwidth,
    '顺势而为': strategy_ma,
    'KDJ极限': strategy_kdj,
    'KDJ绿线': strategy_kdj2,
    'KDJ肖氏': strategy_kdj3,
    '随机漫步': strategy_rnd,
    '正弦变换': strategy_ht_sine,
    '正弦变换2': strategy_ht_sine2,
    '机器学习': strategy_ml,
    '三个综合': strategy_three,
    '五个综合': strategy_five,
}

