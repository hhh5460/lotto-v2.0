import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.widgets import MultiCursor

import numpy as np

import talib as ta
import fc3d_1
import strategy
import strategy2

import time

import logging

logging.basicConfig(level=logging.INFO) #CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET


# 程序界面
class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")
        
        self.setupUI()
        
        self.lt = fc3d_1.FC3D(name='3d') # 彩票类型 ['3d', 'p3', 'kl30'] ['福彩3D','体彩排列3','快乐30分']
        self.lt.load_data(period=500)
        
        self.print_last_label()
    
    
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
        subframe1.pack()
        self.bai, self.shi, self.ge = tk.StringVar(), tk.StringVar(), tk.StringVar()
        tk.Checkbutton(subframe1, text='', onvalue='百', offvalue='', variable=self.bai, command=self.update_combobox1).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='十', offvalue='', variable=self.shi, command=self.update_combobox1).pack(side=tk.LEFT)
        tk.Checkbutton(subframe1, text='', onvalue='个', offvalue='', variable=self.ge, command=self.update_combobox1).pack(side=tk.LEFT)
        
        
        # 第二行：指标
        self.rowframe2 = tk.Frame(labelframe_zhibiao)
        self.rowframe2.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe2, text="指标", width=leftwidth).pack(side=tk.LEFT)
        
        self.zbname = tk.StringVar() # 指标名
        self.combobox1 = ttk.Combobox(self.rowframe2, textvariable=self.zbname, width=rightwidth)
        self.combobox1['values'] = []
        #combobox1.values = ['单双','大小','质合','随机','给定','模','分','路数','跨度','距离','与前差','前期','冷热','三六','组选']
        #self.combobox1.current(0)
        self.combobox1.pack(fill="x")
        
        self.combobox1.bind("<<ComboboxSelected>>", self.show_hide_rowframe_3_4)
        
        
        # 第三行：参数1   --> 用于 mod, fen / jl, yqc / hot
        self.rowframe3 = tk.Frame(labelframe_zhibiao)
        #self.rowframe3.pack(fill="x", ipadx=1, ipady=1)
        self.label_cs1 = tk.Label(self.rowframe3, text="", width=leftwidth) # text="模/分/之前/加权"
        self.label_cs1.pack(side=tk.LEFT)
        
        self.canshu1 = tk.IntVar() # 参数1  若hot,切换为tk.StringVar()
        self.combobox2 = ttk.Combobox(self.rowframe3, textvariable=self.canshu1, width=rightwidth)
        self.combobox2['values'] = [2,4,6,8,10,12,16]
        self.combobox2.current(0)
        #self.combobox2.pack(fill="x")
        
        self.combobox2.bind("<<ComboboxSelected>>", lambda e:self.update_rowframe_4())
        self.combobox2.bind("<Return>", lambda e:self.update_rowframe_4())
        
        # 没办法了，貌似切换IntVar与StringVar不行！！
        # 那就切换combobox与combobox_
        self.jiaquan_type = tk.StringVar()
        self.combobox2_ = ttk.Combobox(self.rowframe3, textvariable=self.jiaquan_type, width=rightwidth)
        self.combobox2_['values'] = ['xx', 'tl', 'zs', 'js', 'tf'] # 线性加权，泰勒加权，指数加权，计数加权，1-0加权
        self.combobox2_.current(0)
        #self.combobox2_.pack(fill="x")
        
        
        
        # 第四行：参数2   --> 用于 mod, fen/ rnd, in_/ zx
        self.rowframe4 = tk.Frame(labelframe_zhibiao)
        #self.rowframe4.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe4, text="数组", width=leftwidth).pack(side=tk.LEFT)
        
        self.canshu2 = tk.StringVar() # 参数2 '[2,4,6,8,10,12,16]'
        ttk.Entry(self.rowframe4, textvariable=self.canshu2, width=rightwidth).pack(side=tk.LEFT)
        ttk.Button(self.rowframe4, text='.',width=1,command=self.update_rowframe_4).pack(side=tk.LEFT)

        
        
        # 第五行：同反
        rowframe5 = tk.Frame(labelframe_zhibiao)
        rowframe5.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe5, text="同反", width=leftwidth).pack(side=tk.LEFT)
        self.tf = tk.IntVar()
        combobox3 = ttk.Combobox(rowframe5, textvariable=self.tf, state='normal', width=rightwidth)
        combobox3['values'] = (0,1,2,3,4,5)
        combobox3.current(0)
        combobox3.pack(fill="x")
        
        
        # ===========================
        # 策略
        # ===========================
        labelframe_strategy = tk.LabelFrame(self, text='策略', fg='blue')
        labelframe_strategy.pack(fill="x", pady=4)
        
        # 按钮
        #frame_button_zhibiao = tk.Frame(labelframe_strategy)
        #frame_button_zhibiao.pack(fill="x")
        #ttk.Button(frame_button_zhibiao, text='simple', command=self.simple).pack(side=tk.RIGHT)
        
        # 第六行：策略名
        self.rowframe6 = tk.Frame(labelframe_strategy)
        self.rowframe6.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe6, text="名称", width=leftwidth).pack(side=tk.LEFT)
        self.strategy_name = tk.StringVar()
        combobox4 = ttk.Combobox(self.rowframe6, textvariable=self.strategy_name, state='normal', width=rightwidth)
        combobox4['values'] = ['KDJ肖氏','KDJ绿线','均线差分','金叉死叉','顺势而为','通道宽度','KDJ极限','随机漫步','三个综合','五个综合','正弦变换','正弦变换2','机器学习','敬请期待...']
        combobox4.current(0)
        combobox4.pack(fill="x")
        
        combobox4.bind("<<ComboboxSelected>>", self.show_hide_rowframe7) # 根据所选值显示/隐藏 机器学习 下拉列表
        
        # 第七行：机器学习
        self.rowframe7 = tk.Frame(labelframe_strategy)
        self.label7 = tk.Label(self.rowframe7, text="机学", width=leftwidth)
        self.label7.pack(side=tk.LEFT)
        self.ml_name = tk.StringVar()
        self.combobox5 = ttk.Combobox(self.rowframe7, textvariable=self.ml_name, state='normal', width=rightwidth)
        self.combobox5['values'] = ['ALL', 'AdaBoost', 'Bagging', 'ExtraTrees', 'GradientBoost', 'RandomForest',
                               'Voting', 'bayies', 'KNeighbors', 'svc', 'DecisionTree', 'ExtraTree',
                               'sk_nn', 'feature_selection1', 'feature_selection2', 'GridSearch', 'RandomizedSearch', 'nn']
        self.combobox5.current(0)
        self.combobox5.pack(fill="x")
        
        #self.rowframe7.pack(fill="x", ipadx=1, ipady=1)
        #self.label7.config(state=tk.DISABLED)    # 禁用
        #self.combobox5.config(state=tk.DISABLED) # 禁用
        
        # 第八行：策略按钮
        rowframe8 = tk.Frame(labelframe_strategy)
        rowframe8.pack(fill='x', ipadx=1, ipady=1)
        ttk.Button(rowframe8, text="使用策略", command=self.use_strategy).pack(side=tk.RIGHT)
        frame_button = tk.Frame(rowframe8)
        frame_button.pack(side=tk.RIGHT)
        self.is_backtest = tk.BooleanVar()
        tk.Checkbutton(frame_button, text="回测", variable=self.is_backtest, onvalue=True, offvalue=False, width=8).pack()
        
        # 第九行：两个按钮
        rowframe9 = tk.Frame(labelframe_strategy)
        rowframe9.pack(fill='x',ipadx=1, ipady=1)
        ttk.Button(rowframe9, text="对比", command=self.compare).pack(side=tk.RIGHT)
        #ttk.Button(rowframe9, text="MA_KDJ", command=self.ma_kdj).pack(side=tk.RIGHT)
        #ttk.Button(rowframe9, text="策略切换", command=self.switch).pack(side=tk.RIGHT)
        #ttk.Button(rowframe9, text="RndErr10+", command=self._find_gt_10_error).pack(side=tk.RIGHT)
        ttk.Button(rowframe9, text="肖氏方法", command=self.xiaos_way).pack(side=tk.RIGHT)
        
        
        # ==========================================
        # 数据
        # ==========================================
        updateframe = tk.LabelFrame(self, text='数据', fg='blue')
        updateframe.pack(fill="x", pady=4)
        
        
        
        # 第十行：最后一期
        rowframe10 = tk.Frame(updateframe)
        rowframe10.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(rowframe10, text="当前", width=leftwidth).pack(side=tk.LEFT)
        
        self.last_label = tk.Label(rowframe10, text="数据尚未加载...", width=rightwidth+3)
        self.last_label.pack(side=tk.LEFT)
        
        # 第十一行：数据来源
        self.rowframe11 = tk.Frame(updateframe)
        self.rowframe11.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(self.rowframe11, text="来源", width=leftwidth).pack(side=tk.LEFT)
        self.data_source = tk.StringVar()
        combobox6 = ttk.Combobox(self.rowframe11, textvariable=self.data_source, state='normal', width=rightwidth)
        combobox6['values'] = ['开彩网','彩皇网']
        combobox6.current(0)
        combobox6.pack(fill="x")
        
        # 第十二行：加载/更新
        rowframe12 = tk.Frame(updateframe)
        rowframe12.pack(fill='x', ipadx=1, ipady=1)
        ttk.Button(rowframe12, text="更新", command=self.update_last).pack(side=tk.RIGHT)


        
        
    def update_combobox1(self):
        wei = ''.join((self.bai.get(),self.shi.get(),self.ge.get()))
        loc = self.lt.get_loc(wei)
        star = loc.count('1')
        #print(loc, star)
        self.wei = wei # 用于画图的标题
        self.loc = loc
        self.star = star
        
        if star == 1:
            self.combobox1['values'] = ['单双*','大小*','质合*','随机','给定']
        elif star == 2:
            self.combobox1['values'] = ['组选#','单双*','大小*','质合*','模','分','路数','跨度','距离','与前差','前期','冷热','随机','给定']
        elif star == 3:
            self.combobox1['values'] = ['三六#','组选#','模','分','路数','跨度','距离','与前差','前期','冷热','随机','给定']
        
        
    # 切换显示/隐藏
    def show_hide_rowframe_3_4(self, event):
        #print(event.widget.get())
        #if event.widget.get() in ['单双','大小','质合','路数','跨度','前期','冷热','三六']:
        self.rowframe3.pack_forget()
        self.rowframe4.pack_forget()
        
        if event.widget.get() in ['模','分']:
            self.rowframe3.pack(after=self.rowframe2, fill="x", ipadx=1, ipady=1)
            self.rowframe4.pack(after=self.rowframe3, fill="x", ipadx=1, ipady=1)
            
            self.combobox2.pack(fill='x')
            self.combobox2_.pack_forget()
            
            self.label_cs1.config(text=event.widget.get())
            #self.canshu1 = tk.IntVar() # 切换类型
            self.combobox2['values'] = [2,4,6,8,10,12,16]
            self.combobox2.current(0)
            
            self.update_rowframe_4() ####################
        elif event.widget.get() in ['距离','与前差']:
            self.rowframe3.pack(after=self.rowframe2, fill="x", ipadx=1, ipady=1)
            
            self.combobox2.pack(fill='x')
            self.combobox2_.pack_forget()
            
            self.label_cs1.config(text="之前")
            #self.canshu1 = tk.IntVar() # 切换类型
            self.combobox2['values'] = [1]
            self.combobox2.current(0)
        elif event.widget.get() in ['冷热']:
            self.rowframe3.pack(after=self.rowframe2, fill="x", ipadx=1, ipady=1)
            
            self.combobox2.pack_forget()
            self.combobox2_.pack(fill='x')
            
            self.label_cs1.config(text="加权")
        elif event.widget.get() in ['随机','给定','组选#']:
            self.rowframe4.pack(after=self.rowframe2, fill="x", ipadx=1, ipady=1)
            
            self.update_rowframe_4() ####################
            
    
    def update_rowframe_4(self):
        sname = self.zbname.get()
        self.lt.set_star_type_maxnumeber(loc=self.loc, zb_name=self.lt.get_zb_name(sname))
        
        list_funcs = {'模':self.lt.get_mod_list,
                      '分':self.lt.get_fen_list,
                      '随机':self.lt.get_rnd_list,
                      '给定':self.lt.get_a_list,
                      '组选#':self.lt.get_zx_list,
        }
        
        if self.zbname.get() in ['模','分']:
            mf = self.canshu1.get() # m/f
            res = str(list_funcs[sname](mf))
        elif self.zbname.get() in ['随机','给定','组选#']:
            res = str(list_funcs[sname]())
            
        #print(res)
        self.canshu2.set(res)
        
    
    # 切换显示/隐藏 机器学习 下拉列表
    def show_hide_rowframe7(self, event):
        #print(event.widget.get())
        if event.widget.get() == '机器学习':
            self.rowframe7.pack(after=self.rowframe6, fill="x", ipadx=1, ipady=1)
            #self.label7.config(state=tk.NORMAL) # 启用
            #self.combobox5.config(state=tk.NORMAL)
        else:
            self.rowframe7.forget()
            #self.label7.config(state=tk.DISABLED) # 禁用
            #self.combobox5.config(state=tk.DISABLED)
        
    
    
    # 切换策略
    def switch(self):
        series = self.get_series()
        
        r = strategy2.switch_strategy(series, '通道宽度', 'KDJ红线')
        
        fig, axes = plt.subplots(1, 1, sharex=True)
        #ax1, ax2, ax3, ax4 = axes[0], axes[1], axes[2], axes[3]
        
        axes.plot(r, 'r-')
        
        plt.show()
        
    
    # 使用策略
    def use_strategy(self):
        #global strategy_name, is_backtest
        self._use_strategy(self.strategy_name.get(), self.is_backtest.get())
        
        
    # 使用策略
    def _use_strategy(self, strategy_name, is_backtest):
        '''12期均线与20期均线交点作为入场信号'''
        #global lt,wan,qian,bai,shi,ge,zbname,tf,ml_name
        
        show_period = 121
        
        series = self.get_series()
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
                axes[1].plot([0,show_period-1],[mean, mean],'k',alpha=.2)
            elif strategy_name == '顺势而为':   # <===============================>
                order, earn, ma = strategy.strategy_ma(series, is_backtest=True)
                axes[1].plot(ma[-show_period:], 'r-')
            elif strategy_name == 'KDJ极限':    # <===============================>
                order, earn, fastk, fastd = strategy.strategy_kdj(series, is_backtest=True)
                axes[1].plot(fastk[-show_period:], 'r-')
                axes[1].plot(fastd[-show_period:], 'g-')
                axes[1].plot([0,show_period-1],[5, 5],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[95, 95],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[30, 30],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[70, 70],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[50, 50],'k',alpha=.2)
            elif strategy_name == 'KDJ绿线':    # <===============================>
                order, earn, fastk, fastd = strategy.strategy_kdj2(series, is_backtest=True)
                axes[1].plot(fastk[-show_period:], 'r-')
                axes[1].plot(fastd[-show_period:], 'g-')
                axes[1].plot([0,show_period-1],[5, 5],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[95, 95],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[30, 30],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[70, 70],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[50, 50],'k',alpha=.2)
            elif strategy_name == 'KDJ肖氏':    # <===============================>
                order, earn, fastk, fastd = strategy.strategy_kdj3(series, is_backtest=True)
                axes[1].plot(fastk[-show_period:], 'r-')
                axes[1].plot(fastd[-show_period:], 'g-')
                axes[1].plot([0,show_period-1],[5, 5],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[95, 95],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[30, 30],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[70, 70],'k',alpha=.2)
                axes[1].plot([0,show_period-1],[50, 50],'k',alpha=.2)
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
            
            title1 = '指标：' + self.wei + '位 ' + self.zbname.get() + ' 同反：' + str(self.tf.get())
            title2 = '策略：' + strategy_name
            if strategy_name == '机器学习':
                title2 += '--' + self.ml_name.get()
            axes[0].set_title(title1, fontproperties="SimHei")
            axes[1].set_title(title2, fontproperties="SimHei")
            axes[2].set_title('投注', fontproperties="SimHei")
            axes[3].set_title('收益', fontproperties="SimHei")
            
            #axes[3].set_xticks(range(120)) # 120个数据
            #axes[3].set_xticklabels(self.get_labels(self.lt.last_period), rotation=35)  # 设置x轴标签（13个）
            #axes[3].xaxis.set_major_locator(MultipleLocator(10))  # 主坐标：间隔10
            
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
    
    def _find_gt_10_error(self):
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
        
    def find_gt_10_error(self):
        '''找出当前（最近）错误已达10期的随机指标对应的rnd_list'''
        assert self.zbname.get() == '随机' # 先选中随机指标
        
        errorperiod = 0
        while errorperiod < 10:
            rnd_list = self.lt.get_rnd_list()
            series = self.lt.adapter(self.loc, 'rnd', (rnd_list,), tf_n=0)
            order, *_ = strategy.strategies[self.strategy_name.get()](series, is_backtest=True)
            errorperiod = max([strategy.times.index(x) for x in order[-10:]])
        
        return rnd_list

    def xiaos_way(self):
        '''肖的方法'''
        print('开始：', time.asctime())
        t0 = time.time()
        
        
        show_period = 121
        
        df = self.lt.df
        self.lt.df = df.head(300)
        
        error_periods = 0 # 哨兵：之前错误期数
        earn = []           # 收益记录
        order = []          # 投注资金记录
        
        for i in df.index[-200:]:
            if error_periods == 0:
                # 拿到满足条件的随机数组
                rnd_list = self.find_gt_10_error()
            
            # 下单
            order.append(strategy.times[error_periods])
            
            # 更新一期数据
            self.lt.df.ix[i] = df.ix[i].tolist() # 通过ix赋值只能是原生list!
            
            # 判断对错
            if self.lt.get_number_series().index[-1] in rnd_list:
                error_periods = 0
                earn.append(1.97 * order[-1]) # 赔率odds=1.96 
            else:
                error_periods += 1
                earn.append(0)
        
        print('投注记录:\n', order[-show_period:], '\n合计：', sum(order[-show_period:]))
        print('收益记录:\n', earn[-show_period:], '\n合计：', sum(earn[-show_period:]))
        print('收益率：', (sum(earn[-show_period:]) - sum(order[-show_period:]))/sum(order[-show_period:]))
        
        fig, axes = plt.subplots(2, 1, sharex=True)
        
        axes[0].plot(order[-show_period:], 'r-')
        #axes[3].plot(np.cumsum(earn[-show_period:])-np.cumsum(order[-show_period:]), 'g-')
        axes[1].fill_between(np.arange(show_period), 0, np.cumsum(earn[-show_period:])-np.cumsum(order[-show_period:]), facecolor="#00FF00", alpha=.7)
        
        axes[0].set_title('投注', fontproperties="SimHei")
        axes[1].set_title('收益', fontproperties="SimHei")
        
        t = time.time() - t0
        print('结束', time.asctime())
        print('耗时：{}分{}秒'.format(int(t)//60, int(t)%60))
        
        multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2], axes[3]), color='b', lw=2)
        
        plt.show()
        
        
    # 六个策略 投注线 对比
    def compare(self):
        '''比较同一指标下的六个策略'''
        show_period = 120
        
        #global lt,wan,qian,bai,shi,ge,zbname,tf
        print('开始：', time.asctime())
        t0 = time.time()
        
        series = self.get_series()
        close = np.cumsum(series).astype(float)
        
        fig, axes = plt.subplots(7, 1, sharex=True)
        #ax1, ax2, ax3, ax4 = axes[0], axes[1], axes[2], axes[3]
        
        
        # 布林线
        upperband, middleband, lowerband = ta.BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        axes[0].plot(close[-show_period:], 'rd-', markersize = 5)
        axes[0].plot(upperband[-show_period:], 'y-')
        axes[0].plot(middleband[-show_period:], 'b-')
        axes[0].plot(lowerband[-show_period:], 'y-')
        title1 = '指标：' + self.wei + '位 ' + self.zbname.get() + ' 同反：' + str(self.tf.get())
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
        
        
        series = self.get_series()
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

        
        title1 = '指标：' + self.wei + '位 ' + self.zbname.get() + ' 同反：' + str(self.tf.get())
        axes[0].set_title(title1, fontproperties="SimHei")
        #axes[1].set_title('金叉死叉', fontproperties="SimHei")
        #axes[2].set_title('均线', fontproperties="SimHei")
        #axes[3].set_title('KDJ绿线', fontproperties="SimHei")

        #axes[4].set_xticks(range(120)) # 120个数据
        #axes[4].set_xticklabels(self.get_labels(self.lt.last_period), rotation=35)  # 设置x轴标签（13个）
        #axes[4].xaxis.set_major_locator(MultipleLocator(10))  # 主坐标：间隔10
        
        t = time.time() - t0
        print('结束', time.asctime())
        print('耗时：{}分{}秒'.format(int(t)//60, int(t)%60))
        
        multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2], axes[3], axes[4]), color='b', lw=2)
        
        plt.show()
        
    # 更新数据
    def update_last(self):
        
        update_funcs = {
            '开彩网': self.lt.update_data_from_API,
            '彩皇网': self.lt.update_data_from_917500,
            #...
        }
        update_funcs[self.data_source.get()]() # 执行更新
        
        self.print_last_label()
        
        
    # ['单双','大小','质合','随机','给定','模','分','路数','跨度','距离','与前差','前期','冷热','三六','组选']
    def get_args(self):
        sname = self.zbname.get()
        
        if sname in ['距离','与前差']:
            self.lt.pre_n = self.canshu1.get()
            
        if sname in ['单双*','大小*','质合*','路数','跨度','前期','三六#','距离','与前差']:
            args = ()
        elif sname in ['模','分']:
            args = (self.canshu1.get(), eval(self.canshu2.get()))
        elif sname in ['随机','给定','组选#']:
            args = (eval(self.canshu2.get()),)
        elif sname in ['冷热']:
            args = (self.jiaquan_type.get(),)
            
        return args
    
    
    def get_series(self):
        series = self.lt.adapter(loc = self.loc,
                                 zb_name = self.lt.get_zb_name(self.zbname.get()), 
                                 args = self.get_args(), 
                                 tf_n = self.tf.get())
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
    
    root.title(" 福彩3D")
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

