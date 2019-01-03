import pandas as pd
import numpy as np
import random
import os

import lunar

import collections

# 六合彩
class Marksix(object):
    colors = [[1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46], # 红(17)
              [5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49],   # 绿(16)
              [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48]]    # 篮(16)
              
    wuxing = [[],[],[],[],[]] # 五行
    
    # ========================
    # 初始化
    # ========================
    def __init__(self, name='marksix'):
        self.name = name
        self.df = None
        
        self.nl_year_sx = lunar.Lunar().sx_year() # 当前农历生肖年
        
        self.max_number = 49
        
        #self.ZS_LIST = [1,2,3,5,7]  # 常量，用于指标：['zh']
        self.pre_n = 1 # 变量，用于指标：['jl','yqc']
        self.presx_type = '平特' # 变量，用于指标：['presx', 'hotsx']，另一个值为：'单列'
        
        self.current_up_numbers =  [] # 当前指标向上号码 -----|
        self.current_down_numbers = [] # 当前指标向下号码     |----> 这三个用于选号
        self.all_numbers = {} # 所有选中的指标对应的号码 -----|
        
        self.curent_qishu = None # 当前期数 （需要联网）
        
        self.zb_name = None # 当前指标名称
        self.loc = '0000001'
        
        #['rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','bs','x6','zx','zxsx','presx','hotsx']
        self.zb_funcs = {
                        'rnd':self.rnd,
                        'in_':self.in_,
                        'mod':self.mod,
                        'fen':self.fen,
                        'ls':self.ls,
                        'kd':self.kd,
                        'jl':self.jl,
                        'yqc':self.yqc,
                        'pre':self.pre,
                        'hot':self.hot,
                        'bs':self.bs,
                        'x6':self.x6,
                        'zx':self.zx,
                        'zxsx':self.zxsx,
                        'presx':self.presx,
                        'hotsx':self.hotsx}
                        
    @property
    def last_draw(self):
        # 最后一期数据，如：20160705001 8 8 8
        res = str(self.df.index[-1]) + ' ' + ' '.join(map(str,self.df.values[-1]))
        return res
        
        
    # 设置
    def set_config(self, **kwargs):
        self.__dict__.update(kwargs)


    # 构造: 星位loc 返回 如：'0000001'
    def get_loc(self, wei='七'):
        res = ''
        for x in '一二三四五六七':
            if x in wei:
                res += '1'
            else:
                res += '0'
        return res
    
    # 构造: 指标名 返回 如：'mod'
    def get_zb_name(self, name='模'):
        names = ['随机','给定','模','分','路数','跨度','距离','与前差','前期','冷热','波色','六肖','组选','组选生肖','前期生肖','冷热生肖']
        zb_names = ['rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','bs','x6','zx','zxsx','presx','hotsx']
        
        #names_dict = {'随机':'rnd','给定':'in_','模':'mod','分':'fen','路数':'ls','跨度':'kd','距离':'jl','与前差':'yqc','前期':'pre','冷热':'hot','波色':'bs','六肖':'x6','组选':'zx','组选生肖':'zxsx'}
        return dict(zip(names, zb_names)).get(name, '')
    
    
    # 下面四个函数，在adapter之前运行
    def get_mod_list(self, m=2):
        if m % 2 == 0:
            mod_list = list(range(m//2, m))
        else:
            mod_list = [i for i in range(m) if i%2 != m%2]
        return mod_list
            
    def get_fen_list(self, f=2):
        fen_list = [i for i in range(f) if i%2 != f%2]
        return fen_list
            
    def get_rnd_list(self):
        n = self.max_number + 1
        rnd_list = sorted(random.sample(range(1, n), n//2))
        return rnd_list
        
    def get_a_list(self):
        n = self.max_number + 1
        a_list = sorted(random.sample(range(1, n), n//2))
        return a_list
        
    def get_x6_list(self):
        x6_list = random.sample(range(0, 12), 6)
        return sorted(x6_list)
        
    def get_bs_list(self, current_color='r'):
        ix = 'rgb'.index(current_color)
        ix_list = [0,1,2]
        del ix_list[ix]
        bs_list = self.colors[ix_list[0]] + list(filter(lambda x:x%2==0, self.colors[ix])) # 取一波半
        return bs_list
            
    # 感觉zx_list最好事先转化为集合，先不管--------
    def get_zx_list(self):
        '''
        选7个号：C(49,7)=85.9kk+, C(45,7)=45.3kk+, C(44,7)=38.3kk+
        '''
        zx_list = random.sample(range(1, 50), 44)
        return sorted(zx_list)
        
    def get_zxsx_list(self):
        '''
        选7个位置的生肖：C(12,7) + 6*C(12,6) + C(12,5)*(C(5,2) + C(5,1)) + C(12,4)*(C(4,3) + 2*C(4,2) + C(4,1)) + C(12,3)*(...)
        '''
        zx_list = random.sample(range(0, 12), 11)
        return sorted(zx_list)
    
    # ========================
    # 转化
    # ========================
    # 根据位置、类型，生成用于计算指标的num，支持一星、二星、及以上!!!
    def get_number_series(self):
        '''
        df.apply(func, axis=1, args=(?,))
        s.apply(func, args=(?,))
        '''
        df = self.df.copy() # 先复制self.df
        
        if self.zb_name in ['zxsx', 'zx']:
            return df
        else:
            return df.iloc[:, self.loc.index('1')]
    

    def adapter(self, loc, zb_name, args=(), tf_n=0):
        '''指标适配器，生成指标序列'''
        # 如果指标名：['jl', 'yqc']，self.pre_n=1（默认1）要事先设置
        
        #['rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','bs','x6','zx','zxsx']
        #self.set_star_type_maxnumeber(loc, zb_name)
        
        zb_func = self.zb_funcs[zb_name]
        
        # 目的：可重现
        self.set_config(loc = loc,
                        zb_name = zb_name,
                        args = args,
                        tf_n = tf_n)
        
        n = self.max_number
        
        series_of_number = self.get_number_series() # 把用于计算指标的数字准备好先 支持一星，及以上
        
        if zb_name in ['rnd','in_','mod','fen','ls','kd','bs','x6']:
            # 都是静态参数
            #assert isinstance(series_of_number, pd.Series)
            series = series_of_number.apply(zb_func, args=args)
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x, *args), range(1,n+1))))) #向上
            down = np.array(list(set(range(1, n+1)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['jl', 'yqc']:
            series = (series_of_number - series_of_number.shift(self.pre_n)).apply(zb_func, args=args)
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x - series_of_number.tail(1), *args), range(1,n+1))))) #向上 （注意tail）
            down = np.array(list(set(range(1, n+1)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['pre', 'hot']:
            series = [0] * n       # 简单粗暴
            for i in range(n, len(series_of_number)):
                pre_list = series_of_number[i-n:i]
                series.append(zb_func(series_of_number[i], pre_list, *args)) # 注意这里：*args
            #print(pre_list[-5:])
            series = pd.Series(series) # 转换为pd.Series类型
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x, series_of_number.tail(n), *args), range(1,n+1))))) #向上 （注意tail）
            down = np.array(list(set(range(1, n+1)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['presx', 'hotsx']:
            if self.presx_type == '平特':
                nn = 2
            elif self.presx_type == '单列':
                nn = 12
            series = [0] * nn       # 2行，平特肖都算在里面
            for i in range(nn, len(series_of_number)):
                if self.presx_type == '平特':
                    pre_list = self.df.iloc[i-nn:i]
                elif self.presx_type =='单列':
                    pre_list = series_of_number[i-n:i]
                series.append(zb_func(series_of_number[i], pre_list, *args)) # 注意这里：*args
            #print(pre_list[-5:])
            series = pd.Series(series) # 转换为pd.Series类型
            
            # 最后，把号码也对应保存
            if self.presx_type == '平特':
                up = np.array(list(set(filter(lambda x:zb_func(x, self.df.tail(nn), *args), range(1,n+1))))) #向上 （注意tail）
            elif self.presx_type == '单列':
                up = np.array(list(set(filter(lambda x:zb_func(x, series_of_number.tail(nn), *args), range(1,n+1))))) #向上 （注意tail）
            down = np.array(list(set(range(1, n+1)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['zxsx', 'zx']:
            assert isinstance(series_of_number, pd.DataFrame)
            series = series_of_number.apply(zb_func, args=args, axis=1)
            
            # 最后，把号码也对应保存
            #a = [[x // 100, (x // 10) % 10, x % 10] for x in range(1000)]
            #up = np.array(list(set(filter(lambda x:zb_func(x, series_of_number.values[-n:], *args), range(n))))) #向上 （pd.Series不支持负数index）
            #down = np.array(list(set(range(n)) - set(up))) #向下
            #self.current_up_numbers = up[np.argsort(up)]
            #self.current_down_numbers = down[np.argsort(down)]
            
        
        # 把0转换为-1    
        series = np.where(series==0, -1, 1).astype(int)
        if tf_n == 0:
            return series
        else:
            return self.tf(series, tf_n)
        
        
    def tf(self, series, tf_n=1):
        '''同反'''
        pre_res = np.repeat(np.array([-1]), tf_n)
        res = np.where(series[:-tf_n] == series[tf_n:], 1, -1)
        return np.hstack((pre_res, res))
    
    # ========================
    # 数据
    # ========================
    def load_data(self, period=500):
        #self.df = pd.DataFrame(np.random.randint(10, size=(period, 3)), columns=list('ABC')) # 伪造3D历史数据！
        self.df = pd.read_csv('marksix.csv', sep=',', header=None, usecols=[0,2,3,4,5,6,7,8], index_col=0, names=['Date','A','B','C','D','E','F','G']).tail(period) #时间作索引
    
    # 更新数据（# 开彩网API）
    def update_data_from_API(self):
        '''更新一期'''
        import requests
        
        url = 'http://f.apiplus.cn/fc3d-1.json' # 开彩网API开放平台http://www.opencai.net/
        
        r = requests.get(url)
        
        rr = r.json() # 格式:{"rows":1,"code":"fc3d","info":"免费接口随机延迟3-5分钟，实时接口请访问opencai.net或QQ:9564384(注明彩票或API)","data":[{"expect":"2016288","opencode":"0,1,0","opentime":"2016-10-21 20:32:00","opentimestamp":1477053120}]}
        
        expect = rr['data'][0]['expect'] # "2016288"
        opentime = rr['data'][0]['opentime'] # "2016-10-21 20:32:00"
        opencode = rr['data'][0]['opencode'] # "0,1,0"
        
        res = '{} {} {}\n'.format(expect, opentime[:10], opencode.replace(',',' '))
        
        fullfilename = os.path.join(os.path.dirname(__file__), 'fc3d.csv')
        with open(fullfilename, 'a', encoding='utf-8') as f:
            f.write(res)
            
        self.load_data()
    
    # 更新数据（彩皇网）
    def update_data_from_917500(self):
        '''更新多期（下载文件，并暴力替换）'''
        import requests 
        
        url = 'http://data.917500.cn/fc3d2000.txt' 
        r = requests.get(url) 
        
        with open("fc3d.csv", "wb", encoding='utf-8') as code:
             code.write(r.content)
                
        self.load_data()

    # ========================
    # 特码 指标函数
    # ========================
    def rnd(self, num, rnd_list): # 静态参数
        '''随机'''
        return 1 if num in rnd_list else 0

    def in_(self, num, a_list): # 静态参数
        '''给定数组'''
        return 1 if num in a_list else 0
    
    def mod(self, num, m, mod_list): # 静态参数
        '''模'''
        return 1 if num % m in mod_list else 0   # 这里是0，方便选号。列操作时改回-1

    def fen(self, num, f, fen_list): # 静态参数
        '''分'''
        max_number = self.max_number
        return 1 if num // ((max_number + 1) / f) in fen_list else 0

    def ls(self, num):
        '''路数'''
        shi, ge = ((num // 10) % 10) % 3, (num % 10) % 3
        return 1 if (shi * ge == 0 and shi + ge != 0) else 0 # 单零路
    
    def kd(self, num):
        '''跨度'''
        wei = [(num // 10) % 10, num % 10]
        return 1 if max(wei) - min(wei) in [0,4,5,6,7,8,9] else 0
        
    def jl(self, sub): # 注意参数sub
        '''距离'''
        # 相对指标
        max_number = self.max_number
        return 1 if max_number/4 < np.abs(sub) < 3 * max_number/4 else 0

    def yqc(self, sub): # 注意参数sub
        '''与前差'''
        # 相对指标
        return 1 if sub > 0 else 0

    def pre(self, num, pre_list): # 动态参数
        '''前期'''
        # 相对指标
        return 1 if num in pre_list.values else 0 # in 运算符处理pandas.Series类型，跟list与numpy.array不一样

    
    def hot(self, num, pre_list, jiaquan_type): # 动态参数 + 静态参数
        '''冷热'''
        # 相对指标
        # 五种情况：线性加权，泰勒加权，指数加权，计数加权，1-0加权 ['xx', 'tl', 'zs', 'js', 'tf']
        n_numbers = self.max_number # 号码个数

        tmp = [0] * n_numbers # 记录对应位置的权重
        for i, x in enumerate(pre_list):
            if jiaquan_type == 'xx':
                tmp[x-1] += i / sum(range(n_numbers))
            elif jiaquan_type == 'tl':
                tmp[x-1] += 1 / (n_numbers - i + 1)
            elif jiaquan_type == 'zs':
                tmp[x-1] += 1 / 2**(n_numbers - i)
            elif jiaquan_type == 'js':
                tmp[x-1] += 1
            elif jiaquan_type == 'tf': #等同于pre
                tmp[x-1] = 1

        tmp = list(zip(range(1, n_numbers+1), tmp))
        tmp.sort(key=lambda x:x[1], reverse=True)
        ttmp = [x[0] for x in tmp[:n_numbers//2]] # 找出最热的一半号码
        
        return 1 if num in ttmp else 0
    
    def presx(self, num, pre_list): # 动态参数
        '''前期生肖'''
        return 1 if (num % 12) in (pre_list.values % 12) else 0
        
    def hotsx(self, num, pre_list): # 动态参数      未实现
        '''冷热生肖'''
        #hotsx_list = []
        #return (num % 12) in collections.Counter(pre_list.values.flatten()).most_common()
        
        # 未实现，先用这个顶着
        return 1 if (num % 12) in (pre_list.values % 12) else 0
        
        
    def get_hotsx_sort(self, pre_list):
        '''取生肖的冷热排位'''
        hotsx_list = [0] * 12  # 12个生肖
        if isinstance(pre_list, pd.core.series.Series):
            pass
        elif isinstance(pre_list, pd.core.series.DataFrame):
            pass
    
    def bs(self, num, bs_list): # 静态参数
        '''波色'''
        # 一波半
        #print(bs_list)
        return 1 if num in bs_list else 0
    
    def x6(self, num, x6_list): # 静态参数
        '''六肖'''
        return 1 if (num % 12) in x6_list else 0
    
    # ========================
    # 平特 指标函数
    # ========================
    def zxsx(self, nums, zxsx_list): # 静态参数
        '''组选生肖'''
        # 七个位置
        return 1 if set(nums % 12).issubset(set(zxsx_list)) else 0
    
    
    def zx(self, nums, zx_list): # 静态参数
        '''组选'''
        # 七个位置
        # C(49,7)/2 = C(45,7)-,    C(49,7)/2 = C(44,7)+
        return 1 if set(nums).issubset(set(zx_list)) else 0
        
    
    # 辅助函数
    # 返回今年生肖序列
    def conver_sx(self):
        sx = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
        
        new_sx = list(sx)
        new_sx.reverse()
        new_sx = ''.join(new_sx)
        
        ix = new_sx.index(self.nl_year_sx)
        if ix >= 1:
            new_sx = new_sx[ix-1:] + new_sx[:ix-1]
        else:
            new_sx = new_sx[-1] + new_sx[:-1]
        
        return new_sx

# 测试
def test():
    lt = Marksix()
    lt.load_data(period=500)
    
    m = 2
    series = lt.adapter(loc='0000001', zb_name='mod', args=(m, lt.get_mod_list(m)), tf_n=0)
    print('mod\t', series.sum())
    f = 2
    series = lt.adapter(loc='0000001', zb_name='fen', args=(f, lt.get_fen_list(f)), tf_n=0)
    print('fen\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='ls', args=(), tf_n=0)
    print('ls\t', series.sum())
    series = lt.adapter(loc='0000001', zb_name='kd', args=(), tf_n=0)
    print('kd\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='jl', args=(), tf_n=0)
    print('jl\t', series.sum())
    series = lt.adapter(loc='0000001', zb_name='yqc', args=(), tf_n=0)
    print('yqc\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='pre', args=(), tf_n=0)
    print('pre\t', series.sum())
    jiaquan_type='xx'
    series = lt.adapter(loc='0000001', zb_name='hot', args=(jiaquan_type,), tf_n=0)
    print('hot\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='x6', args=(lt.get_x6_list(),), tf_n=0)
    print('pre\t', series.sum())
    current_color = 'r'
    series = lt.adapter(loc='0000001', zb_name='bs', args=(current_color,), tf_n=0)
    print('hot\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='rnd', args=(lt.get_rnd_list(),), tf_n=0)
    print('rnd\t', series.sum())
    series = lt.adapter(loc='0000001', zb_name='in_', args=(lt.get_rnd_list(),), tf_n=0)
    print('in_\t', series.sum())
    
    series = lt.adapter(loc='0000001', zb_name='zx', args=(lt.get_zx_list(),), tf_n=0)
    print('zx\t', series.sum())
    series = lt.adapter(loc='0000001', zb_name='zxsx', args=(lt.get_zxsx_list(),), tf_n=0)
    print('zxsx\t', series.sum())
    

if __name__ == '__main__':
    #test()
    
    lt = Marksix()
    lt.load_data(period=500)
    #series = lt.adapter(loc='0000001', zb_name='pre', args=(), tf_n=0)
    
    
    # 统计特码每12期有多少个生肖
    s = lt.df['G'] % 12
    
    res = []
    for i in range(12, len(s)):
        res.append(len(set(s[i-12:i])))
        
    c = collections.Counter(res).most_common()
    print(c)
    print(res[-20:])
    
    
    # 统计平特码每2期有多少个生肖
    df = lt.df.copy() % 12
    res = []
    for i in range(2, len(df)):
        res.append(len(set(df[i-2:i].values.flatten())))
        
    c = collections.Counter(res).most_common()
    print(c)
    print(res[-20:])