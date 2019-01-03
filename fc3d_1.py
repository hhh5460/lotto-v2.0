import pandas as pd
import numpy as np
import random
import os


# 福彩3D
class FC3D(object):
    # ========================
    # 初始化
    # ========================
    def __init__(self, name='3d'):
        self.name = name
        self.df = None
        
        self.ZS_LIST = [1,2,3,5,7]  # 常量，用于指标：['zh']
        self.pre_n = 1 # 变量，用于指标：['jl','yqc']
        
        self.current_up_numbers =  [] # 当前指标向上号码 -----|
        self.current_down_numbers = [] # 当前指标向下号码     |----> 这三个用于选号
        self.all_numbers = {} # 所有选中的指标对应的号码 -----|
        
        self.curent_qishu = None # 当前期数 （需要联网）
        #self.curent_zb_name = None # 当前指标名称
        
        #['m2','f2','zh','rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','z3z6','zx']
        self.zb_funcs = {'m2':self.m2,
                        'f2':self.f2,
                        'zh':self.zh,
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
                        'z3z6':self.z3z6,
                        'zx':self.zx}
                        
    @property
    def last_draw(self):
        # 最后一期数据，如：20160705001 8 8 8
        res = str(self.df.index[-1]) + ' ' + ' '.join(map(str,self.df.values[-1]))
        return res
        
        
    # 设置
    def set_config(self, **kwargs):
        self.__dict__.update(kwargs)
        
        
    def set_zb_type(self, zb_name='m2'):
        star = self.star
        if zb_name in ['m2','f2','zh']:
            zb_type = 0
        elif zb_name in ['mod','fen','ls','kd','jl','yqc','pre','hot']:
            zb_type = 1
        elif zb_name in ['z3z6','zx']:
            zb_type = 2
        elif zb_name in ['rnd','in_']:
            if star == 1:
                zb_type = 0
            else:
                zb_type = 1
        self.zb_type = zb_type
        
        
    def set_star(self, loc='001'):
        self.star = loc.count('1')
        
    def set_max_number(self):
        zb_type = self.zb_type
        if zb_type == 0:
            self.max_number = 9 # 即使 loc='011'。因为此时计算和数尾数！！
        else:
            self.max_number = 10**self.star - 1
            
    def set_star_type_maxnumeber(self, loc='001', zb_name='m2'):
        self.set_star(loc)
        self.set_zb_type(zb_name)
        self.set_max_number()
        

    # 构造: 星位loc 返回 如：'00011'
    def get_loc(self, wei='十个'):
        res = ''
        for x in '百十个':
            if x in wei:
                res += '1'
            else:
                res += '0'
        return res
    
    # 构造: 指标名 返回 如：'m2'
    def get_zb_name(self, name='单双*'):
        names = ['单双*','大小*','质合*','随机','给定','模','分','路数','跨度','距离','与前差','前期','冷热','三六#','组选#']
        zb_names = ['m2','f2','zh','rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','z3z6','zx']
        
        #names_dict = {'单双':'m2','大小':'f2','质合':'zh','随机':'rnd','给定':'in_','模':'mod','分':'fen','路数':'ls','跨度':'kd','距离':'jl','与前差':'yqc','前期':'pre','冷热':'hot','三六':'z3z6','组选':'zx'}
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
        rnd_list = sorted(random.sample(range(n), n//2))
        return rnd_list
        
    def get_a_list(self):
        n = self.max_number + 1
        a_list = sorted(random.sample(range(n), n//2))
        return a_list
            
    # 感觉zx_list最好事先转化为集合，先不管--------
    def get_zx_list(self):
        '''
        一星：C(10,1)=10, C(5,1)=5
        二星：C(10,2) + C(10,1)=45 + 10=55, C(7,2) + C(7,1)=21+7=29
        三星：C(10,3) + 2*C(10,2) + C(10,1)=120+2*45+10=220, C(8,3) + 2*C(8,2) + C(8,1)=56+2*28+8=120
        '''
        if self.zb_type  == 0:
            zx_list = random.sample(range(10), 5)
        else:
            if self.star  == 2:
                zx_list = random.sample(range(10), 7)
            elif self.star == 3:
                zx_list = random.sample(range(10), 8)
        return sorted(zx_list)
    
    # ========================
    # 转化
    # ========================
    # 根据位置、类型，生成用于计算指标的num，支持一星、二星、及以上!!!
    def get_number_series(self):
        '''
        如：
        self.loc = '101'，则先取：self.df['A','C']
        zb_type的值有三个，
        若zb_type = 0：返回df['A','C']
        若zb_type = 1：返回pd.Series (对于号码548，得到 5*10+8 = 58（两位数）)
        若zb_type = 2：返回pd.Series (对于号码548，返回 (5+8)%10 = 3（一位数）)
        
        目的：
        方便使用
        df.apply(func, axis=1, args=(?,))
        s.apply(func, args=(?,))
        '''
        
        # 方式一
        df = self.df.copy() # 先复制self.df
        for l,c in zip(self.loc, self.df.columns):
            if l == '0': del df[c] # 删除列
            
        # 方式二
        #df = pd.DataFrame() # 先空DataFrame!!!
        #for l,c in zip(self.loc, self.df.columns):
        #    if l == '1': df[c] = self.df[c] # 添加列
        
        # 根据self.zb_type，决定返回值
        if self.zb_type == 2:
            return df
        elif self.zb_type == 1:
            n = df.columns.size
            des = [10**(n-1-i) for i in range(n)] # 位权，如[100,10,1]
            s = 0 # 小技巧，最终s是pd.Series！！
            for c,d in zip(df.columns, des):
                s += df[c] * d
            return s
        elif self.zb_type == 0: # 否则，取和尾
            s = 0 # 同上
            for c in df.columns:
                s += df[c]
            s = s % 10
            return s
    

    def adapter(self, loc, zb_name, args=(), tf_n=0):
        '''指标适配器，生成指标序列'''
        # 如果指标名：['jl', 'yqc']，self.pre_n=1（默认1）要事先设置
        
        #['m2','f2','zh','rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','z3z6','zx']
        self.set_star_type_maxnumeber(loc, zb_name)
        
        zb_func = self.zb_funcs[zb_name]
        
        # 目的：可重现
        self.set_config(loc = loc,
                        zb_name = zb_name,
                        args = args,
                        tf_n = tf_n)
        
        n = self.max_number + 1
        
        series_of_number = self.get_number_series() # 把用于计算指标的数字准备好先 支持一星，及以上
        
        if zb_name in ['m2','f2','zh','mod','fen','ls','kd','rnd','in_']:
            # 都是静态参数
            #assert isinstance(series_of_number, pd.Series)
            series = series_of_number.apply(zb_func, args=args)
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x, *args), range(n))))) #向上
            down = np.array(list(set(range(n)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['jl', 'yqc']:
            series = (series_of_number - series_of_number.shift(self.pre_n)).apply(zb_func, args=args)
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x - series_of_number.values[-1], *args), range(n))))) #向上 （pd.Series不支持负数index）
            down = np.array(list(set(range(n)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['pre', 'hot']:
            series = [0] * n
            for i in range(n, len(series_of_number)):
                pre_list = series_of_number[i-n:i]
                series.append(zb_func(series_of_number[i], pre_list, *args)) # 注意这里：*args
            series = pd.Series(series) # 转换为pd.Series类型
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x, series_of_number.values[-n:], *args), range(n))))) #向上 （pd.Series不支持负数index）
            down = np.array(list(set(range(n)) - set(up))) #向下
            self.current_up_numbers = up[np.argsort(up)]
            self.current_down_numbers = down[np.argsort(down)]
        elif zb_name in ['z3z6', 'zx']:
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
        self.df = pd.read_csv('fc3d.csv', sep=' ', header=None, usecols=[1,2,3,4], index_col=0, names=['Date','A','B','C']).tail(period) #时间作索引
    
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
    # 指标函数
    # ========================
    # ------------------------
    # 适用：zb_type == 2
    # ------------------------
    def m2(self, num):
        '''单双'''
        return num % 2   # 这里是0，方便选号。列操作时改回 -1
        
    def f2(self, num):
        '''大小'''
        return 1 if num >= 5 else 0
        
    def zh(self, num):
        '''质合'''
        return 1 if num in self.ZS_LIST else 0
        
    # ------------------------
    # 适用：zb_type == 2,1
    # ------------------------
    def rnd(self, num, rnd_list):
        '''随机'''
        return 1 if num in rnd_list else 0

    def in_(self, num, a_list):
        '''给定数组'''
        return 1 if num in a_list else 0
        
    # ------------------------
    # 适用：zb_type == 1
    # ------------------------
    def mod(self, num, m, mod_list):
        '''模'''
        return 1 if num % m in mod_list else 0   # 这里是0，方便选号。列操作时改回-1

    def fen(self, num, f, fen_list):
        '''分'''
        max_number = self.max_number
        return 1 if num // ((max_number + 1) / f) in fen_list else 0

    def ls(self, num):
        '''路数'''
        # 各个位置的路数之和
        bai, shi, ge = [(num // 100) % 3, ((num // 10) % 10) % 3, (num % 10) % 3]
        if self.zb_type == 0:
            return 1 if ge in [0] else 0 # 4:6
        else:
            if self.star == 2:
                return 1 if shi + ge in [2, 3] else 0 # 51:49
            elif self.star == 3:
                return 1 if bai + shi + ge in [2, 3] else 0 # 495:505
    
    def kd(self, num):
        '''跨度'''
        if self.zb_type == 0:
            # 此时 跨度 等同于 大小！
            wei = [num % 10, 0] # 小伎俩：0
        else:
            if self.star == 2:
                wei = [num // 10, num % 10]
            elif self.star == 3:
                wei = [num // 100, (num // 10) % 10, num % 10]
        return 1 if max(wei) - min(wei) in [5,6,7,8,9] else 0
        
    def jl(self, sub): # 注意参数sub
        '''距离'''
        # 相对指标
        max_number = self.max_number
        return 1 if max_number/4 < np.abs(sub) < 3 * max_number/4 else 0

    def yqc(self, sub): # 注意参数sub
        '''与前差'''
        # 相对指标
        return 1 if sub > 0 else 0

    def pre(self, num, pre_list):
        '''前期'''
        # 相对指标
        return 1 if num in pre_list else 0
    
    def hot(self, num, pre_list, jiaquan_type):
        '''冷热'''
        # 相对指标
        # 五种情况：线性加权，泰勒加权，指数加权，计数加权，1-0加权 ['xx', 'tl', 'zs', 'js', 'tf']
        n_numbers = self.max_number + 1 # 号码个数

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

        tmp = list(zip(range(n_numbers), tmp))
        tmp.sort(key=lambda x:x[1], reverse=True)
        ttmp = [x[0] for x in tmp[:n_numbers//2]] # 找出最热的一半号码
        
        return 1 if num in ttmp else 0
    
    # ------------------------
    # 适用：zb_type == 0
    # ------------------------
    def z3z6(self, nums):
        '''组三组六'''
        return 1 if pd.unique(nums).size == 3 else 0

    def zx(self, nums, zx_list):
        '''组选'''
        #C(10,3)/2 ~= C(8,3)，C(10,2)/2 ~= C(7,2)，C(10,1)/2 ~= C(7,1)，C(49,7)/2 ~= C(45,7)
        return 1 if set(nums).issubset(set(zx_list)) else 0

# 测试
def test():
    lt = FC3D()
    lt.load_data(period=1000)
    
    series = lt.adapter(loc='001', zb_name='m2', args=(), tf_n=1)
    print('m2\t', series.sum())
    series = lt.adapter(loc='011', zb_name='m2', args=(), tf_n=0)
    print('m2\t', series.sum())
    
    m = 2
    series = lt.adapter(loc='011', zb_name='mod', args=(m, lt.get_mod_list(m)), tf_n=0)
    print('mod\t', series.sum())
    f = 2
    series = lt.adapter(loc='011', zb_name='fen', args=(f, lt.get_fen_list(f)), tf_n=0)
    print('fen\t', series.sum())
    
    series = lt.adapter(loc='011', zb_name='ls', args=(), tf_n=0)
    print('ls\t', series.sum())
    series = lt.adapter(loc='011', zb_name='kd', args=(), tf_n=0)
    print('kd\t', series.sum())
    
    series = lt.adapter(loc='011', zb_name='jl', args=(), tf_n=0)
    print('jl\t', series.sum())
    series = lt.adapter(loc='011', zb_name='yqc', args=(), tf_n=0)
    print('yqc\t', series.sum())
    
    series = lt.adapter(loc='011', zb_name='pre', args=(), tf_n=0)
    print('pre\t', series.sum())
    jiaquan_type='xx'
    series = lt.adapter(loc='011', zb_name='hot', args=(jiaquan_type,), tf_n=0)
    print('hot\t', series.sum())
    
    
    series = lt.adapter(loc='011', zb_name='rnd', args=(lt.get_rnd_list(),), tf_n=0)
    print('rnd\t', series.sum())
    series = lt.adapter(loc='011', zb_name='in_', args=(lt.get_rnd_list(),), tf_n=0)
    print('in_\t', series.sum())
    
    zx_list = lt.get_zx_list()
    series = lt.adapter(loc='011', zb_name='zx', args=(zx_list,), tf_n=0)
    print('zx\t', series.sum())
    series = lt.adapter(loc='111', zb_name='z3z6', args=(), tf_n=0)
    print('z3z6\t', series.sum())
    
def test2():
    lt = FC3D()
    #lt.load_data(period=1000)
    
    lt.set_star_type_maxnumeber(loc='011', zb_name='mod')
    print('mod_list 2', lt.get_mod_list(2))
    print('mod_list 3', lt.get_mod_list(3))
    print('mod_list 4', lt.get_mod_list(4))
    print('mod_list 5', lt.get_mod_list(5))
    print('mod_list 6', lt.get_mod_list(6))
    print('mod_list 7', lt.get_mod_list(7))
    print('mod_list 8', lt.get_mod_list(8))
    print('mod_list 9', lt.get_mod_list(9))
    print('mod_list 10', lt.get_mod_list(10))
    
    lt.set_star_type_maxnumeber(loc='011', zb_name='fen')
    print('fen_list 2', lt.get_fen_list(2))
    print('fen_list 3', lt.get_fen_list(3))
    print('fen_list 4', lt.get_fen_list(4))
    print('fen_list 5', lt.get_fen_list(5))
    print('fen_list 6', lt.get_fen_list(6))
    print('fen_list 7', lt.get_fen_list(7))
    print('fen_list 8', lt.get_fen_list(8))
    print('fen_list 9', lt.get_fen_list(9))
    print('fen_list 10', lt.get_fen_list(10))
    
    lt.set_star_type_maxnumeber(loc='011', zb_name='rnd')
    print('rnd_list', lt.get_rnd_list())
    
    lt.set_star_type_maxnumeber(loc='011', zb_name='in_')
    print('a_list 2', lt.get_a_list())
    
    lt.set_star_type_maxnumeber(loc='011', zb_name='zx')
    print('zx_list 2', lt.get_zx_list())

if __name__ == '__main__':
    test2()