import numpy as np
import pandas as pd
import os

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
import datetime
from io import StringIO


# 时时彩
class SSC(object):
    def __init__(self, name='cq', type='00001'):
        self.name = name # ['cq', 'xj', 'tj'] ['重庆','新疆','天津']
        self.type = type
        #self.star = star
        
        self.current_up_numbers =  [] # 当前指标向上号码 -----|
        self.current_down_numbers = [] # 当前指标向下号码     |----> 这三个用于选号
        self.all_numbers = {} # 所有选中的指标对应的号码 -----|
        
        #self.curent_qishu = None # 当前期数 （需要联网）
        self.curent_zb_name = None # 当前指标名称
        #self.last_draw = None #最后一期数据
        
        self.zb_funcs = {
            'm2': self.m2, #单双
            'f2': self.f2, #大小
            'zh': self.zh,  #质合
            'rnd': self.rnd, #随机
            'in_': self.in_  #给定数组
        }
    
    @property
    def last_draw(self):
        # 最后一期数据，如：20160705001 88888
        res = str(self.df.index[-1]) + ' ' + ''.join(map(str,self.df.values[-1]))
        return res
    
    @property
    def last_period(self):
        # 最后一期期号
        res = self.df.index[-1] % 1000
        return res
    
    @property
    def star(self):
        return self.type.count('1')
        
        
    def set_config(self, **kwargs):
        self.__dict__.update(kwargs)
        
        
    # 构造: 星位type 返回 如：'00011'
    def get_type(self, loc='十个'):
        res = ''
        for x in '万千百十个':
            if x in loc:
                res += '1'
            else:
                res += '0'
        return res
    
    # 构造: 指标名 返回 如：'m2'
    def get_name(self, name='单双'):
        names_dict = {'单双':'m2','大小':'f2','质合':'zh','随机':'rnd','给定':'in_'}
        return names_dict.get(name, '')
    
    # 生成用于计算指标的num，支持一星，及以上!!!
    def get_num(self):
        '''
        根据type生成用于计算指标的num，支持一星，及以上!!!
        如： type = '00011'
        且： 号码 = '22458'
        则：num = (5 + 8) % 10 = 13 % 10 = 3
        
        如： type = '00001'
        且： 号码 = '22458'
        则：num = 8 % 10 = 8
        '''
        des = 1
        nums = 0 # 注意：其实最终nums是DataFrame!!!
        for t,c in zip(reversed(self.type), reversed(self.df.columns)):
            if t == '1':
                nums += self.df[c] * des
        return nums % 10
    
    def get_last_draw(self):
        '''日中：取最新一期数据'''
        
        
        #彩皇网
        #url = 'http://917500.cn/Home/Lottery/kaijianghao/lotid/cqssc.html?page=1&nourl=1'
        url = 'http://917500.cn/Home/Lottery/kaijianghao/lotid/cqssc.html?nourl=true'

        
        headers = {
            'Host': '917500.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://917500.cn/Home/Award/all.html',
            'Cookie': 'pgv_pvi=8829466624; PHPSESSID=579p17bq0rucq6tl9ia20uq676; tishi=1; pgv_si=s9473959936',
            'DNT': '1',
            'Connection': 'keep-alive'
        }

        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, 'html.parser')

        #网页结构
        #<tr>
        #  <td>20160613023</td>
        #  <td>2016-06-13 01:55</td>
        #  <td><em>3,1,8,8,9</em></td>
        #</tr>

        td1 = soup.find('td')
        td3 = td1.find_next().find_next()
        last_period_text = td1.get_text('', strip=True)
        last_draw_text = td3.get_text('', strip=True)
        print('last_period_text: ', last_period_text)
        print('last_draw_text: ', last_draw_text)
        
        last_period = np.fromstring(last_period_text, dtype=np.int64, sep=' ')
        last_draw = np.fromstring(last_draw_text, dtype=np.int64, sep=',')
        print('last_period: ', last_period)
        print('last_draw: ', last_draw)
        
        if last_period[0] - self.df.index[-1] == 0:
            print('网站未更新'.center(50,'-'))
        elif last_period[0] - self.df.index[-1] == 1.: # 若刚好相差一期==================================
            self.df.set_value(last_period[0], list('ABCDE'), last_draw)
            self.df = self.df.astype(np.int64)
            
            self.n_periods = self.df.shape[0]
            print('已更新一期'.center(50,'*'))
        else:
            self.get_draws_from_917500_txt() #如果期数不相隔1，那就重新下载全部数据
            #self.get_draws_from_baidu_lecai()
            #self.get_draws_from_shishicai()
            print('已更新全部'.center(50,'@'))
    
    # 重庆福彩
    def get_last_draw_cqcp(self):

        url = "http://www.cqcp.net/game/ssc/"

        r = requests.get(url)

        soup = BeautifulSoup(r.text, 'html.parser')

        # 获取期数
        div = soup.find('div', id='openlist')
        ul = div.find('ul')
        
        # 特别地，记录最新的期数
        ul2 = ul.find_next_sibling() # 第二个ul开始
        li = ul2.find('li') # 第一个li是期数，如：161004039
        last_period = int('20' + li.get_text(strip=True))

        # 提取全部十行记录，不管它了！
        res = []
        for i in range(10):
            ul2 = ul.find_next_sibling() # 第二个ul开始

            li = ul2.find('li') # 第一个li是期数，如：161004039
            li2 = li.find_next_sibling() # 第二个li是号码，如：1-2-3-4-5

            period = li.get_text(strip=True)
            draw = li2.get_text(strip=True)

            res.append('20' + period + ' ' + draw.replace('-', ' ') + '\n') # 20161004039 1 2 3 4 5\n
            #print(res)
            
        # 顺序反过来
        res = res[::-1]
        
        n = last_period - self.df.index[-1]
        print('已更新{}期'.format(n).center(50,'*'))
        
        if 0 < n <= 10:
            new_df = pd.read_csv(StringIO(''.join(res[:n])), sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
            self.df = pd.concat([self.df, new_df])
        elif n > 10:
            self.get_draws_from_917500_txt() #如果期数相隔超10，那就重新下载全部数据

    
    def get_draws_from_917500_txt(self, period=400):
        '''日始：生成真实历史数据（能联网）
        2016/06/16网站停止更新，
        2016/08/11网站又更新'''
        # 参数period只能为下列值[400, 1000, 2000, 10000]
        # 如：http://917500.cn/data/cqssc_400.txt
        url = r'http://917500.cn/data/{}ssc_{}.txt'.format(self.name, period) # 彩煌网
        
        # 格式：20160531115 8 8 8 1 8
        #self.df = np.genfromtxt(url, delimiter=' ')
        self.df = pd.read_csv(url, sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
        
        self.n_periods = self.df.shape[0]
        
        
    def get_draws_from_baidu_lecai(self):
        '''日始：生成真实历史数据（百度乐彩）'''
        

        url = 'http://hao123.lecai.com/lottery/draw/sorts/ajax_get_draw_data.php'

        headers = {
            'Host': 'hao123.lecai.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://hao123.lecai.com/lottery/draw/view/200',
            'Cookie': '_lcas_uuid=1040465692; _adwr=178438497%23http%253A%252F%252Fhao123.lecai.com%252Flottery%252Fcqssc%252F; Hm_lvt_ddaa40fe0ef9967e65e6956736d327af=1470413739; _lhc_uuid=sp_576260f624f439.43965773; Hm_lvt_380c0eb03566ff43dff53ac9c4f155e8=1470848313; __ads_session=h50NCEBWxAjl4nACuwA=; Hm_lpvt_380c0eb03566ff43dff53ac9c4f155e8=1470848648; _adwb=19752481; _adwc=19752481; _adwp=110406678.7733323112.1465763284.1467513736.1470848313.6',
            'DNT': 1,
            'Connection': 'keep-alive'
        }
        
        headers = {
            'Host': 'hao123.lecai.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:48.0) Gecko/20100101 Firefox/48.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://hao123.lecai.com/lottery/draw/view/200',
            'Cookie': '__ads_session=CU7ZcfpLxgjtO98BaAA=; _lhc_uuid=sp_57bef6f22b64f1.09038799; Hm_lvt_380c0eb03566ff43dff53ac9c4f155e8=1472132850; Hm_lpvt_380c0eb03566ff43dff53ac9c4f155e8=1472133070',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }

        #t = time.localtime()
        #year, month, day = t.tm_year, t.tm_mon, t.tm_mday
        
        res = ''
        for i in range(4): 
            day = datetime.date.today() - datetime.timedelta(days=3-i)
            data = {
                'lottery_type': 200,
                'date': day.strftime('%Y-%m-%d')
                #'date':time.strftime('%Y-%m-%d',(year,month,day-3+i,0,0,0,0,0,0))
            }
        
            r = requests.post(url, data=data, headers=headers)
            json = r.json()
            
            tmp = []
            for j in range(120):
                try:
                    draw = json['data']['data'][j]['result']['result'][0]['data'] # ['3', '5', '3', '3', '8']
                    draw = ' '.join(draw) # '3 5 3 3 8'
                    period = json['data']['data'][j]['phase'] # '20160615120'
                    
                    row = period + ' ' + draw + '\n' # '20160615120 3 5 3 3 8\n'
                    tmp.append(row)
                except:
                    #print(j, tmp[0]) #最新一期
                    break
            tmp.reverse()
            res += ''.join(tmp)
            print('日期：{} 下载完成！'.format(data['date']))
            time.sleep(1)
            
        #print(res)
        self.df = pd.read_csv(StringIO(res), sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
        self.n_periods = self.df.shape[0]
    
    def get_draws_from_500(self):
        '''日始：生成真实历史数据（五百万）'''
        root_url = "http://kaijiang.500.com/static/public/ssc/xml/qihaoxml/"
        #url = "http://kaijiang.500.com/static/public/ssc/xml/qihaoxml/20161004.xml"

        res = ''
        for i in range(4):
            day = datetime.date.today() - datetime.timedelta(days=3-i)

            filename = day.strftime('%Y%m%d') + '.xml'
            
            url = root_url + filename
            
            r = requests.get(url)
            
            try:
                root = ET.fromstring(r.text)
            except:
                break
            
            j = 0
            for row in root:
                period, draw = row.attrib['expect'], row.attrib['opencode']# 20161004119 1,2,3,4,5
                if j > 0:
                    res += period + ' ' + draw.replace(',', ' ') + '\n' # 去掉第一行119期（重复！）
                
                j += 1
            
        self.df = pd.read_csv(StringIO(res), sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
        self.n_periods = self.df.shape[0]
        
    
    def get_draws_from_shishicai(self):
        '''日始：生成真实历史数据（时时彩）'''
        import requests
        import time
        import datetime
        from io import StringIO
        
        url = 'http://data.shishicai.cn/handler/kuaikai/data.ashx'

        headers = {
            'Host': 'data.shishicai.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:48.0) Gecko/20100101 Firefox/48.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://data.shishicai.cn/cqssc/haoma/',
            'Content-Length': '25',
            #'Cookie': 'Hm_lvt_cad2e9c6544a1e8f06862d019ce44f71=1468721317,1468981552,1470881560; Html_v_54=df11_63606511509072; ssc_user_LandingPage=http%3a%2f%2fdata.shishicai.cn%2fcqssc%2fhaoma%2f; ssc_user_SiteReferrerUrl=https%3a%2f%2fwww.baidu.com%2flink%3furl%3dRFd4voFK-87jfKXYy8CFQnyqriA5ohmmk0vDC5SiJnkdY7PwSmOSGa3-cWUppSf3%26wd%3d%26eqid%3dfcc40d07000e61b80000000657abdf04; ssc_user_RegEnterPage=http%3a%2f%2fdata.shishicai.cn%2fcqssc%2fhaoma%2f; Hm_lpvt_cad2e9c6544a1e8f06862d019ce44f71=1470881560',
            'Cookie':'Hm_lvt_cad2e9c6544a1e8f06862d019ce44f71=1468981552,1470881560,1470885934,1470891335; Html_v_54=3647_63606522016672; ssc_user_LandingPage=http%3a%2f%2fdata.shishicai.cn%2fcqssc%2fhaoma%2f; ssc_user_SiteReferrerUrl=https%3a%2f%2fwww.baidu.com%2flink%3furl%3dRFd4voFK-87jfKXYy8CFQnyqriA5ohmmk0vDC5SiJnkdY7PwSmOSGa3-cWUppSf3%26wd%3d%26eqid%3dfcc40d07000e61b80000000657abdf04; ssc_user_RegEnterPage=http%3a%2f%2fdata.shishicai.cn%2fcqssc%2fhaoma%2f; Hm_lpvt_cad2e9c6544a1e8f06862d019ce44f71=1470892377',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        res = ''
        for i in range(4): 
            day = datetime.date.today() - datetime.timedelta(days=3-i)
            data = {
                'lottery': 4,
                'date': day.strftime('%Y-%m-%d')
                #'date':time.strftime('%Y-%m-%d',(year,month,day-3+i,0,0,0,0,0,0))
            }
        
            r = requests.post(url, data=data, headers=headers)
            json = r.json()[:-1][::-1] # 这里r.json()返回的是list,奇怪！
            #json == ['20160811-001;32412;2016-08-11 00:05', ...]
            
            res += '\n'.join([x[:8] + x[9:12]+' '+' '.join(list(x[13:18])) for x in json])
            print('日期：{} 下载完成！'.format(data['date']))
            time.sleep(0.5)
            
        #print(res)
        self.df = pd.read_csv(StringIO(res), sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
        self.n_periods = self.df.shape[0]
    
    def get_history(self):
        '''日始：生成真实历史数据（不能联网时）'''
        import os
        filename = '{}ssc_1000.txt'.format(self.name)
        fullfilename = os.path.join(os.path.dirname(__file__), filename)
        self.df = pd.read_csv(fullfilename, sep=' ', header=None, index_col=0, names=['Priod','A','B','C','D','E'])
        
        self.n_periods = self.df.shape[0]
    
    
    # ==========================================
    # 下面是各个指标函数
    # ==========================================
    def adapter(self, zb_name, tf_n, *args):
        '''指标适配器，生成指标序列'''
        # ['m2','f2','zh','rnd','in_']
        self.curent_zb_name = zb_name
        
        zb_func = self.zb_funcs[zb_name]
        
        n = 10**self.star
        
        series_of_number = self.get_num() # 把用于计算指标的数字准备好先 支持一星，及以上
        res = []
        if zb_name in ['rnd']:
            #_, = args
            rnd_list = np.random.choice(np.arange(n), n//2, replace=False)
            
            for x in series_of_number:
                res.append(zb_func(x, ran_list))
                
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x, ran_list), range(n))))) #向上
            self.current_up_numbers = up[np.argsort(up)]
            down = np.array(list(set(range(n)) - set(filter(lambda x:zb_func(x, ran_list), range(n))))) #向下
            self.current_down_numbers = down[np.argsort(down)]
            
        elif zb_name in ['m2','f2', 'zh']:
            #_, = args
            
            for x in series_of_number:
                res.append(zb_func(x))
            
            # 最后，把号码也对应保存
            up = np.array(list(set(filter(lambda x:zb_func(x), range(n))))) #向上
            self.current_up_numbers = up[np.argsort(up)]
            down = np.array(list(set(range(n)) - set(filter(lambda x:zb_func(x), range(n))))) #向下
            self.current_down_numbers = down[np.argsort(down)]
            
        elif zb_name in ['in_']:
            a_list, = args
            
            for x in series_of_number:
                res.append(zb_func(x, a_list))
            
            # 最后，把号码也对应得到
            up = np.array(list(set(filter(lambda x:zb_func(x, a_list), range(n))))) #向上
            self.current_up_numbers = up[np.argsort(up)]
            down = np.array(list(set(range(n)) - set(filter(lambda x:zb_func(x, a_list), range(n))))) #向下
            self.current_down_numbers = down[np.argsort(down)]
        
        series = np.where(np.array(res)==0, -1, 1)
        if tf_n == 0:
            return series
        else:
            return self.tf(series, tf_n)
        
        

    def tf(self, series, tf_n=1):
        '''同反'''
        pre_res = np.repeat(np.array([-1]), tf_n)
        res = np.where(series[:-tf_n] == series[tf_n:], 1, -1)
        return np.hstack((pre_res, res))
    
    # ==========================================
    # 二分指标↓↓↓↑↑→→←←
    # ==========================================
    
    # 单双
    def m2(self, num):
        '''单双'''
        return num % 2   # 这里是0，方便选号。列操作时改回 -1
        
    # 大小
    def f2(self, num):
        '''大小'''
        return 1 if num >= 5 else 0
        
    # 质合
    def zh(self, num):
        '''质合'''
        zs_list = [1,2,3,5,7]
        return 1 if num in zs_list else 0
    
    # 随机
    def rnd(self, num, rnd_list):
        '''随机'''
        return 1 if num in rnd_list else 0


    def in_(self, num, a_list):
        '''给定数组'''
        return 1 if num in a_list else 0


    
if __name__ == '__main__':
    ssc = SSC(name='cq')
    ssc.get_draws_from_baidu_lecai()
    #ssc.get_draws_from_shishicai()
    ssc.set_config(type='00001')
    #ssc.set_params
    #ssc.set_options
    series = ssc.adapter('m2', tf_n=0)
    