import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.widgets import MultiCursor

import numpy as np

import talib as ta
import ssc_1
import strategy

import time


# 程序界面
class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        
        self.setupUI()
        
        self.lt = ssc_1.SSC(name='cq') # 彩票类型 ['cq', 'xj', 'tj'] ['重庆','新疆','天津']

    
    def setupUI(self):
        leftwidth = 6
        rightwidth = 15
        
        # ===========================
        # 指标
        # ===========================
        labelframe_zhibiao = tk.LabelFrame(self, text='指标', fg='blue')
        labelframe_zhibiao.pack(fill="x", pady=4)
        
        # 第一行：星位
        rowframe1 = tk.Frame(labelframe_zhibiao)
        rowframe1.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe1, text="星位", width=leftwidth).pack(side=tk.LEFT)
        
        subframe1 = tk.Frame(rowframe1, width=rightwidth)
        subframe1.pack(fill="x")
        self.wan, self.qian, self.bai, self.shi, self.ge = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        tk.Checkbutton(subframe1, text='', onvalue='万', offvalue='', variable=self.wan).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='千', offvalue='', variable=self.qian).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='百', offvalue='', variable=self.bai).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='十', offvalue='', variable=self.shi).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='个', offvalue='', variable=self.ge).pack(side=tk.LEFT)
        
        # 第二行：指标
        rowframe2 = tk.Frame(labelframe_zhibiao)
        rowframe2.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe2, text="指标", width=leftwidth).pack(side=tk.LEFT)
        
        self.zbname = tk.StringVar() # 指标名
        combobox1 = ttk.Combobox(rowframe2, textvariable=self.zbname, values=['单双','大小','质合','随机','给定'], width=rightwidth)
        combobox1.current(0)
        combobox1.pack(fill="x")
        
        # 第三行：同反
        rowframe3 = tk.Frame(labelframe_zhibiao)
        rowframe3.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe3, text="同反", width=leftwidth).pack(side=tk.LEFT)
        self.tf = tk.IntVar()
        combobox2 = ttk.Combobox(rowframe3, textvariable=self.tf, state='normal', width=rightwidth)
        combobox2['values'] = (0,1,2,3,4,5)
        combobox2.current(0)
        combobox2.pack(fill="x")
        
        
        # ===========================
        # 策略
        # ===========================
        labelframe_strategy = tk.LabelFrame(self, text='策略', fg='blue')
        labelframe_strategy.pack(fill="x", pady=4)
        
        # 按钮
        #frame_button_zhibiao = tk.Frame(labelframe_strategy)
        #frame_button_zhibiao.pack(fill="x")
        #ttk.Button(frame_button_zhibiao, text='simple', command=self.simple).pack(side=tk.RIGHT)
        
        # 第四行：策略名
        rowframe4 = tk.Frame(labelframe_strategy)
        rowframe4.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe4, text="名称", width=leftwidth).pack(side=tk.LEFT)
        self.strategy_name = tk.StringVar()
        combobox3 = ttk.Combobox(rowframe4, textvariable=self.strategy_name, state='normal', width=rightwidth)
        combobox3['values'] = ['KDJ绿线','均线差分','金叉死叉','顺势而为','通道宽度','KDJ极限','随机漫步','三个综合','五个综合','正弦变换','正弦变换2','机器学习','敬请期待...']
        combobox3.current(0)
        combobox3.pack(fill="x")
        
        combobox3.bind("<<ComboboxSelected>>", self.show_hide_rowframe5) # 根据所选值显示/隐藏 机器学习 下拉列表
        
        # 第五行：机器学习
        self.rowframe5 = tk.Frame(labelframe_strategy)
        #self.rowframe5.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe5, text="机学", width=leftwidth).pack(side=tk.LEFT)
        self.ml_name = tk.StringVar()
        combobox4 = ttk.Combobox(self.rowframe5, textvariable=self.ml_name, state='normal', width=rightwidth)
        combobox4['values'] = ['ALL', 'AdaBoost', 'Bagging', 'ExtraTrees', 'GradientBoost', 'RandomForest',
                               'Voting', 'bayies', 'KNeighbors', 'svc', 'DecisionTree', 'ExtraTree',
                               'sk_nn', 'feature_selection1', 'feature_selection2', 'GridSearch', 'RandomizedSearch', 'nn']
        combobox4.current(0)
        combobox4.pack(fill="x")
        
        # 第六行：策略按钮
        self.rowframe6 = tk.Frame(labelframe_strategy)
        self.rowframe6.pack(fill='x', ipadx=1, ipady=1)
        ttk.Button(self.rowframe6, text="使用策略", command=self.use_strategy).pack(side=tk.RIGHT)
        frame_button = tk.Frame(self.rowframe6)
        frame_button.pack(side=tk.RIGHT)
        self.is_backtest = tk.BooleanVar()
        tk.Checkbutton(frame_button, text="回测", variable=self.is_backtest, onvalue=True, offvalue=False, width=8).pack()
        
        # 第七行：两个按钮
        self.rowframe7 = tk.Frame(labelframe_strategy)
        self.rowframe7.pack(fill='x',ipadx=1, ipady=1)
        ttk.Button(self.rowframe7, text="对比", command=self.compare).pack(side=tk.RIGHT)
        #ttk.Button(self.rowframe7, text="MA_KDJ", command=self.ma_kdj).pack(side=tk.RIGHT)
        #ttk.Button(rowframe9, text="策略切换", command=self.switch).pack(side=tk.RIGHT)
        ttk.Button(rowframe9, text="RndErr10+", command=self.find_gt_10_error).pack(side=tk.RIGHT)
        
        
        # ==========================================
        # 数据
        # ==========================================
        updateframe = tk.LabelFrame(self, text='数据', fg='blue')
        updateframe.pack(fill="x", pady=4)
        
        # 第八行：数据来源
        self.rowframe8 = tk.Frame(updateframe)
        self.rowframe8.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe8, text="来源", width=leftwidth).pack(side=tk.LEFT)
        self.data_source = tk.StringVar()
        combobox5 = ttk.Combobox(self.rowframe8, textvariable=self.data_source, state='normal', width=rightwidth)
        combobox5['values'] = ['百度乐彩','五百万','彩煌网','时时彩','旧数据(断网时)']
        combobox5.current(0)
        combobox5.pack(fill="x")
        
        # 第九行：最后一期
        rowframe9 = tk.Frame(updateframe)
        rowframe9.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe9, text="当前", width=leftwidth).pack(side=tk.LEFT)
        
        self.last_label = tk.Label(rowframe9, text="数据尚未加载...", width=rightwidth+3)
        self.last_label.pack(side=tk.LEFT)
        
        # 第十行：加载/更新
        rowframe10 = tk.Frame(updateframe)
        rowframe10.pack(fill='x', ipadx=1, ipady=1)
        self.upd_btn = ttk.Button(rowframe10, text="更新", command=self.update_last)
        self.upd_btn.pack(side=tk.RIGHT)
        self.upd_btn.config(state=tk.DISABLED) # 按钮禁用
        self.load_btn = ttk.Button(rowframe10, text="加载", command=self.load_data)
        self.load_btn.pack(side=tk.RIGHT)
        
        
    # 切换显示/隐藏 机器学习 下拉列表
    def show_hide_rowframe5(self, event):
        #print(event.widget.get())
        if event.widget.get() == '机器学习':
            self.rowframe6.pack_forget()
            self.rowframe7.pack_forget()
            
            self.rowframe5.pack(fill="x", ipadx=1, ipady=1)
            self.rowframe6.pack(fill="x", ipadx=1, ipady=1)
            self.rowframe7.pack(fill="x", ipadx=1, ipady=1)
        else:
            self.rowframe5.pack_forget()

    
    # 使用策略
    def use_strategy(self):
        #global strategy_name, is_backtest
        self._use_strategy(self.strategy_name.get(), self.is_backtest.get())
        
        
    # 使用策略
    def _use_strategy(self, strategy_name, is_backtest):
        '''12期均线与20期均线交点作为入场信号'''
        #global lt,wan,qian,bai,shi,ge,zbname,tf,ml_name
        
        show_period = 120
        
        w,q,b,s,g = self.wan.get(),self.qian.get(),self.bai.get(),self.shi.get(),self.ge.get()
        name, pre_n = self.zbname.get(),self.tf.get()
        loc = ''.join((w,q,b,s,g))
        series = self.get_series(loc, name, pre_n)
        close = np.cumsum(series).astype(float)
        
        if is_backtest:
            print('开始：', time.asctime())
            t0 = time.time()
            
            fig, axes = plt.subplots(4, 1, sharex=True)
            ax1, ax2, ax3, ax4 = axes[0], axes[1], axes[2], axes[3]
        
            # 布林线
            upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
            axes[0].plot(close[-show_period:], 'rd-', markersize = 5)
            axes[0].plot(upperband[-show_period:], 'y-')
            axes[0].plot(middleband[-show_period:], 'b-')
            axes[0].plot(lowerband[-show_period:], 'y-')
            

            if strategy_name == '金叉死叉':     # <===============================>
                order, earn, ma_fast, ma_slow = strategy.strategy_gold_die(series, is_backtest=True)
                axes[1].plot(ma_fast[-show_period:], 'g-')
                axes[1].plot(ma_slow[-show_period:], 'r-')
            elif strategy_name == '均线差分':
                order, earn, ma_fast, ma_slow = strategy.strategy_mean_diff(series, is_backtest=True)
                axes[1].plot(ma_fast[-show_period:], 'g-')
                axes[1].plot(ma_slow[-show_period:], 'r-')
            elif strategy_name == '通道宽度':   # <===============================>
                order, earn, bandwidth, mean = strategy.strategy_bandwidth(series, is_backtest=True)
                axes[1].plot(bandwidth[-show_period:], 'r-')
                axes[1].plot([0,show_period],[mean, mean],'k',alpha=.2)
            elif strategy_name == '顺势而为':   # <===============================>
                order, earn, ma = strategy.strategy_ma(series, is_backtest=True)
                axes[1].plot(ma[-show_period:], 'r-')
            elif strategy_name == 'KDJ极限':    # <===============================>
                order, earn, fastk, fastd = strategy.strategy_kdj(series, is_backtest=True)
                axes[1].plot(fastk[-show_period:], 'r-')
                axes[1].plot(fastd[-show_period:], 'g-')
                axes[1].plot([0,show_period],[5, 5],'k',alpha=.2)
                axes[1].plot([0,show_period],[95, 95],'k',alpha=.2)
            elif strategy_name == 'KDJ绿线':    # <===============================>
                order, earn, fastk, fastd = strategy.strategy_kdj2(series, is_backtest=True)
                axes[1].plot(fastk[-show_period:], 'r-')
                axes[1].plot(fastd[-show_period:], 'g-')
                axes[1].plot([0,show_period],[5, 5],'k',alpha=.2)
                axes[1].plot([0,show_period],[95, 95],'k',alpha=.2)
            elif strategy_name == '随机漫步':   # <===============================>
                order, earn, rnd = strategy.strategy_rnd(series, is_backtest=True)
                axes[1].plot(rnd[-show_period:], 'ro-', markersize=2)
            elif strategy_name == '正弦变换':   # <===============================>
                order, earn, sine, leadsine = strategy.strategy_ht_sine(series, is_backtest=True)
                axes[1].plot(sine[-show_period:], 'r-')
                axes[1].plot(leadsine[-show_period:], 'g-')
            elif strategy_name == '正弦变换2':   # <===============================>
                order, earn, sine, leadsine = strategy.strategy_ht_sine2(series, is_backtest=True)
                axes[1].plot(sine[-show_period:], 'r-')
                axes[1].plot(leadsine[-show_period:], 'g-')
            elif strategy_name == '机器学习':   # <===============================>
                order, earn, ml = strategy.strategy_ml(series, self.ml_name.get(), is_backtest=True)
                axes[1].plot(ml[-show_period:], 'ro-', markersize=2)
            elif strategy_name == '三个综合':   # <===============================>
                order, earn, signals = strategy.strategy_three(series, is_backtest=True)
                axes[1].plot(signals[-show_period:], 'ro-', markersize=2)
            elif strategy_name == '五个综合':   # <===============================>
                order, earn, signals = strategy.strategy_five(series, is_backtest=True)
                axes[1].plot(signals[-show_period:], 'ro-', markersize=2)
            elif strategy_name == '敬请期待':   # <===============================>
                pass
            
            
            axes[2].plot(order[-show_period:], 'r-')
            #axes[3].plot(np.cumsum(earn[-show_period:])-np.cumsum(order[-show_period:]), 'g-')
            axes[3].fill_between(np.arange(show_period), 0, np.cumsum(earn[-show_period:])-np.cumsum(order[-show_period:]), facecolor="#00FF00", alpha=.7)
            
            title1 = '指标：' + loc + '位 ' + name + ' 同反：' + str(pre_n)
            title2 = '策略：' + strategy_name
            if strategy_name == '机器学习':
                title2 += '--' + self.ml_name.get()
            axes[0].set_title(title1, fontproperties="SimHei")
            axes[1].set_title(title2, fontproperties="SimHei")
            axes[2].set_title('投注', fontproperties="SimHei")
            axes[3].set_title('收益', fontproperties="SimHei")
            
            axes[3].set_xticks(range(120)) # 120个数据
            axes[3].set_xticklabels(self.get_labels(self.lt.last_period), rotation=35)  # 设置x轴标签（13个）
            axes[3].xaxis.set_major_locator(MultipleLocator(10))  # 主坐标：间隔10
            
            t = time.time() - t0
            print('结束', time.asctime())
            print('耗时：{}分{}秒'.format(int(t)//60, int(t)%60))
            
            multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2], axes[3]), color='b', lw=2)
            
            plt.show()
        
        else:
            if strategy_name == '金叉死叉':     # <===============================>
                signal = strategy.strategy_gold_die(series, is_backtest=False)
            elif strategy_name == '均线差分':
                signal = strategy.strategy_mean_diff(series, is_backtest=False)
            elif strategy_name == '通道宽度':   # <===============================>
                signal = strategy.strategy_bandwidth(series, is_backtest=False)
            elif strategy_name == '顺势而为':   # <===============================>
                signal = strategy.strategy_ma(series, is_backtest=False)
            elif strategy_name == 'KDJ极限':    # <===============================>
                signal = strategy.strategy_kdj(series, is_backtest=False)
            elif strategy_name == 'KDJ绿线':    # <===============================>
                signal = strategy.strategy_kdj2(series, is_backtest=False)
            elif strategy_name == '随机漫步':   # <===============================>
                signal = strategy.strategy_rnd(series, is_backtest=False)
            elif strategy_name == '正弦变换':   # <===============================>
                signal = strategy.strategy_ht_sine(series, is_backtest=False)
            elif strategy_name == '正弦变换2':   # <===============================>
                signal = strategy.strategy_ht_sine2(series, is_backtest=False)
            elif strategy_name == '机器学习':   # <===============================>
                signal = strategy.strategy_ml(series, self.ml_name.get(), is_backtest=False)
            elif strategy_name == '三个综合':   # <===============================>
                signal = strategy.strategy_three(series, is_backtest=False)
            elif strategy_name == '五个综合':   # <===============================>
                signal = strategy.strategy_five(series, is_backtest=False)
            elif strategy_name == '敬请期待':   # <===============================>
                pass
    
    def find_gt_10_error(self):
        '''找出当前（最近）错误已达10期的随机指标对应的rnd_list'''
        assert self.zbname.get() == '随机' # 先选中随机指标
        
        errorperiod = 0
        while errorperiod < 10:
            rnd_list = self.lt.get_rnd_list()
            series = self.lt.adapter(self.loc, 'rnd', (rnd_list,), tf_n=0)
            order, *_ = strategy.strategies[self.strategy_name.get()](series, is_backtest=True)
            errorperiod = max([strategy.times.index(x) for x in order[-10:]])
        
        print(errorperiod)
        print(rnd_list)
        self.canshu2.set(str(rnd_list)) # 显示在参数2文本框内
    
    # 切换策略
    def switch(self):
        series = self.get_series()
        
        r = strategy2.switch_strategy(series, '通道宽度', 'KDJ红线')
        
        fig, axes = plt.subplots(1, 1, sharex=True)
        #ax1, ax2, ax3, ax4 = axes[0], axes[1], axes[2], axes[3]
        
        axes.plot(r, 'r-')
        
        plt.show()
        
    # 六个策略 投注线 对比
    def compare(self):
        '''比较同一指标下的六个策略'''
        show_period = 120
        
        #global lt,wan,qian,bai,shi,ge,zbname,tf
        print('开始：', time.asctime())
        t0 = time.time()
        
        w,q,b,s,g = self.wan.get(), self.qian.get(), self.bai.get(), self.shi.get(), self.ge.get()
        name, pre_n = self.zbname.get(), self.tf.get()
        loc = ''.join((w,q,b,s,g))
        series = self.get_series(loc, name, pre_n)
        close = np.cumsum(series).astype(float)
        
        fig, axes = plt.subplots(7, 1, sharex=True)
        #ax1, ax2, ax3, ax4 = axes[0], axes[1], axes[2], axes[3]
        
        
        # 布林线
        upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        axes[0].plot(close[-show_period:], 'rd-', markersize = 5)
        axes[0].plot(upperband[-show_period:], 'y-')
        axes[0].plot(middleband[-show_period:], 'b-')
        axes[0].plot(lowerband[-show_period:], 'y-')
        title1 = '指标：' + loc + '位 ' + name + ' 同反：' + str(pre_n)
        axes[0].set_title(title1, fontproperties="SimHei")
        
        stratename = ['金叉死叉','通道宽度','顺势而为','KDJ极限','随机漫步','正弦变换']
        '''strategies = {
            '金叉死叉': strategy_gold_die,
            '通道宽度': strategy_bandwidth,
            '顺势而为': strategy_ma,
            'KDJ极限': strategy_kdj,
            '随机漫步': strategy_rnd,
            '正弦变换': strategy_ht_sine,
        }'''
        order1, earn1, ma_fast, ma_slow = strategy.strategy_gold_die(series, is_backtest=True)
        order2, earn2, bandwidth, mean = strategy.strategy_bandwidth(series, is_backtest=True)
        order3, earn3, ma = strategy.strategy_ma(series, is_backtest=True)
        order4, earn4, fastk, fastd = strategy.strategy_kdj(series, is_backtest=True)
        order5, earn5, rnd = strategy.strategy_rnd(series, is_backtest=True)
        order6, earn6, sine, leadsine = strategy.strategy_ht_sine(series, is_backtest=True)
        for ax, order, name, c in zip(axes[1:],[order1, order2, order3, order4, order5, order6], stratename, 'bgbgbg'):
            ax.plot(order[-show_period:], c+'-')
            ax.set_ylabel(name, fontproperties="SimHei")
            ax.set_ylim([0, 243])

        t = time.time() - t0
        print('结束', time.asctime())
        print('耗时：{}分{}秒'.format(int(t)//60, int(t)%60))
        
        multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2], axes[3], axes[4], axes[5], axes[6]), color='b', lw=2)
        
        plt.show()
        

    # MA 与 KDJ 对比（临时）
    def ma_kdj(self):
        '''对比均线与KDJ绿线，看看能否搞一个新的策略'''
        
        show_period = 120
        
        #global lt,wan,qian,bai,shi,ge,zbname,tf
        print('开始：', time.asctime())
        t0 = time.time()
        
        w,q,b,s,g = self.wan.get(),self.qian.get(),self.bai.get(),self.shi.get(),self.ge.get()
        name, pre_n = self.zbname.get(),self.tf.get()
        loc = ''.join((w,q,b,s,g))
        series = self.get_series(loc, name, pre_n)
        close = np.cumsum(series).astype(float)
        
        fig, axes = plt.subplots(5, 1, sharex=True)
        #fig.set_tight_layout(True)
        
        
        # 布林线
        upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        axes[0].plot(close[-show_period:], 'rd-', markersize = 5)
        axes[0].plot(upperband[-show_period:], 'y-')
        axes[0].plot(middleband[-show_period:], 'b-')
        axes[0].plot(lowerband[-show_period:], 'y-')
        
        #策略：金叉死叉
        order, earn, ma_fast, ma_slow = strategy.strategy_gold_die(series)
        axes[1].plot(ma_fast[-show_period:], 'g-')
        axes[1].plot(ma_slow[-show_period:], 'r-')

        # 策略：KDJ绿线
        order2, earn2, fastk, fastd = strategy.strategy_kdj(series)
        axes[2].plot(fastk[-show_period:], 'r-')
        axes[2].plot(fastd[-show_period:], 'g-')
        # 策略：通道宽度
        order, earn, bandwidth, mean = strategy.strategy_bandwidth(series)
        axes[3].plot(bandwidth[-show_period:], 'r-')
        axes[3].plot([0,show_period],[mean, mean],'k',alpha=.4)
        # 策略：正弦变换
        order, earn, sine, leadsine = strategy.strategy_ht_sine(series)
        axes[4].plot(sine[-show_period:], 'r-')
        axes[4].plot(leadsine[-show_period:], 'g-')

        
        title1 = '指标：' + loc + '位 ' + name + ' 同反：' + str(pre_n)
        axes[0].set_title(title1, fontproperties="SimHei")
        #axes[1].set_title('金叉死叉', fontproperties="SimHei")
        #axes[2].set_title('均线', fontproperties="SimHei")
        #axes[3].set_title('KDJ绿线', fontproperties="SimHei")

        axes[4].set_xticks(range(120)) # 120个数据
        axes[4].set_xticklabels(self.get_labels(self.lt.last_period), rotation=35)  # 设置x轴标签（13个）
        axes[4].xaxis.set_major_locator(MultipleLocator(10))  # 主坐标：间隔10
        
        t = time.time() - t0
        print('结束', time.asctime())
        print('耗时：{}分{}秒'.format(int(t)//60, int(t)%60))
        
        multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2], axes[3], axes[4]), color='b', lw=2)
        
        plt.show()
        
    # 更新数据
    def update_last(self):
        #self.lt.get_last_draw() # 彩皇
        self.lt.get_last_draw_cqcp()# 重庆福彩
        self.print_last_label()
        
        
    # 加载数据
    def load_data(self):
        
        update_funcs = {
            '旧数据(断网时)': self.lt.get_history,
            '彩煌网': self.lt.get_draws_from_917500_txt,
            '百度乐彩': self.lt.get_draws_from_baidu_lecai,
            '时时彩': self.lt.get_draws_from_shishicai,
            '五百万': self.lt.get_draws_from_500,
        }
        
        update_funcs[self.data_source.get()]() # 执行加载
        
        self.print_last_label()
        
        self.load_btn.config(state=tk.DISABLED) # 按钮禁用
        self.upd_btn.config(state=tk.NORMAL) # 按钮启用
        
    # 生成x坐标标签
    def get_labels(self, current_period):
        index1 = ['{:0>2}:{:0>2}'.format(i//60, i%60) for i in range(5, 120, 5)]
        index2 = ['{:0>2}:{:0>2}'.format(i//60, i%60) for i in range(600, 1320+10, 10)]
        index3 = ['{:0>2}:{:0>2}'.format(i//60, i%60) for i in range(1320+5, 1440+5, 5)]
        index = index1 + index2 + index3

        index = index[current_period:] + index[:current_period]
        labels = [None] + index[::10] + [index[0]]
        
        return labels
    
    def get_series(self, loc='个', sname='单双', tf=0):
        #global lt
        type_ = self.lt.get_type(loc) # '00001' 星位
        name = self.lt.get_name(sname) # ['m2','f2','zh','rnd','in_']
        
        self.lt.set_config(type=type_)
        series = self.lt.adapter(name, tf_n=tf)
        #close = np.cumsum(series).astype(float)
        return series
        
    # 更新标签
    def print_last_label(self):
        #global lt, last_label
        self.last_label['text'] = self.lt.last_draw
    

def main():
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1) # Grid管理器允许通过几个方法来控制组件在容器中的位置。weight选项指出一个行或列的相对缩放比例，针对一个行，如果将weight设为3，那么他将以三倍于weight值为1的比例伸展。默认值是0，表明当用户改变窗口大小时，单元格的大小保持不变。
    #root.geometry('640x360')  # 主窗口大小
    root.resizable(width=False, height=False) # 禁止改变大小
    
    root.title(" 时时彩")
    #root.geometry("300x200+10+10") # 宽*长+左位移+右位移
    try:
        root.iconbitmap('taurus.ico')
    except:
        pass
    #root.resizable(False, False)
    #root.minsize(300, 200) # 最小尺寸
    #root.maxsize(600, 400) # 最大尺寸
    #root.attributes("-toolwindow", 1) 
    root.attributes("-topmost", 1) # 置顶窗口
    #root.state("zoomed") # 最大化
    #root.iconify() # 最小化
    #root.deiconify() # 还原最小化
    root.configure(background='black')

    app = AppWindow(root)
    app.mainloop()


if __name__ == "__main__":
    main()

