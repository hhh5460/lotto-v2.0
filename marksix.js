

/**
 ** 警告：此代码具有很强的python风格！！！
 **/

var marksix = (function(){
    //初始化
    var dataframe = [[],[],[],[],[],[],[]], //历史数据
        max_number = 49,
        loc = "0000001",
        pre_n = 1;
        
        
    var sx = '鼠牛虎兔龙蛇马羊猴鸡狗猪';
        
    var colors = [[1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46], // 红(17)
                  [5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49],   // 绿(16)
                  [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48]];   // 篮(16)
        
    var zbfuncs = {
        "rnd": rnd,
        "in_": in_,
        "mod": mod,
        "fen": fen,
        "ls": ls,
        "kd": kd,
        "jl": jl,
        "yqc": yqc,
        "pre": pre,
        "hot": hot
    };
    
    var zbnames = {
        "随机": "rnd",
        "给定": "in_",
        "模": "mod",
        "分": "fen",
        "路数": "ls",
        "跨度": "kd",
        "距离": "jl",
        "与前差": "yqc",
        "前期": "pre",
        "冷热": "hot"
    };
    
    /**
     * ==============================
     * 数据函数
     * ==============================
     */
    //转置
    function t(arr){
        var res = [[],[],[],[],[],[],[]];
        for (var i in arr){
            for (var j in arr[0]){
                res[j][i] = arr[i][j]
            }
        }
        return res;
    };
    
    //加载数据（伪造）
    function load_data2(timeperiod=500){
        arr = get_range(0,timeperiod).map(function(x){return get_sample(get_range(1,50), 7);}) //500期数据
        //console.log(arr);
        
        dataframe = t(arr)// 转置
        //console.log(dataframe);
    };
    
    //加载数据（真实）
    function load_data(){				//得到号码历史数据，然后修改dataLength。    -----------ajax
		if (window.XMLHttpRequest){   //IE7+, Firefox, Chrome, Opera, Safari
			xmlhttp = new XMLHttpRequest();
		}else{                        //IE6, IE5
			xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
		}
        
		xmlhttp.open("GET","marksix.xml",false);
		xmlhttp.send();
		xmlDoc = xmlhttp.responseXML; 
        
		var x = xmlDoc.getElementsByTagName("Record");
		for (var i=0; i<x.length; i++) { 
			var xrow = x[i];
			for(var j=0; j<9; j++){ 
				if(navigator.appName!=="Netscape"){                                    //检查浏览器
					dataframe[j][i] = xrow.childNodes[j].childNodes[0].nodeValue;     //0,1,2,3,...Error for Chrome,but IE
				}else{
					dataframe[j][i] = xrow.childNodes[2*j+1].childNodes[0].nodeValue; //1,3,5,7,...OK  for Chrome,but IE
				}
			}
		}
		
	};
    
    //更新数据
    function update_data(last_period){
        //方法：post，参数：last_period
    };
    
    
    
    /**
     * ==============================
     * 辅助函数
     * ==============================
     */
    //传入公历日期对象，返回年份生肖
    function getSxYear(objDate){
        //日期资料
        var lunarInfo=[
                        0x4bd8,0x4ae0,0xa570,0x54d5,0xd260,0xd950,0x5554,0x56af,0x9ad0,0x55d2,
                        0x4ae0,0xa5b6,0xa4d0,0xd250,0xd295,0xb54f,0xd6a0,0xada2,0x95b0,0x4977,
                        0x497f,0xa4b0,0xb4b5,0x6a50,0x6d40,0xab54,0x2b6f,0x9570,0x52f2,0x4970,
                        0x6566,0xd4a0,0xea50,0x6a95,0x5adf,0x2b60,0x86e3,0x92ef,0xc8d7,0xc95f,
                        0xd4a0,0xd8a6,0xb55f,0x56a0,0xa5b4,0x25df,0x92d0,0xd2b2,0xa950,0xb557,
                        0x6ca0,0xb550,0x5355,0x4daf,0xa5b0,0x4573,0x52bf,0xa9a8,0xe950,0x6aa0,
                        0xaea6,0xab50,0x4b60,0xaae4,0xa570,0x5260,0xf263,0xd950,0x5b57,0x56a0,
                        0x96d0,0x4dd5,0x4ad0,0xa4d0,0xd4d4,0xd250,0xd558,0xb540,0xb6a0,0x95a6,
                        0x95bf,0x49b0,0xa974,0xa4b0,0xb27a,0x6a50,0x6d40,0xaf46,0xab60,0x9570,
                        0x4af5,0x4970,0x64b0,0x74a3,0xea50,0x6b58,0x5ac0,0xab60,0x96d5,0x92e0,
                        0xc960,0xd954,0xd4a0,0xda50,0x7552,0x56a0,0xabb7,0x25d0,0x92d0,0xcab5,
                        0xa950,0xb4a0,0xbaa4,0xad50,0x55d9,0x4ba0,0xa5b0,0x5176,0x52bf,0xa930,
                        0x7954,0x6aa0,0xad50,0x5b52,0x4b60,0xa6e6,0xa4e0,0xd260,0xea65,0xd530,
                        0x5aa0,0x76a3,0x96d0,0x4afb,0x4ad0,0xa4d0,0xd0b6,0xd25f,0xd520,0xdd45,
                        0xb5a0,0x56d0,0x55b2,0x49b0,0xa577,0xa4b0,0xaa50,0xb255,0x6d2f,0xada0,
                        0x4b63,0x937f,0x49f8,0x4970,0x64b0,0x68a6,0xea5f,0x6b20,0xa6c4,0xaaef,
                        0x92e0,0xd2e3,0xc960,0xd557,0xd4a0,0xda50,0x5d55,0x56a0,0xa6d0,0x55d4,
                        0x52d0,0xa9b8,0xa950,0xb4a0,0xb6a6,0xad50,0x55a0,0xaba4,0xa5b0,0x52b0,
                        0xb273,0x6930,0x7337,0x6aa0,0xad50,0x4b55,0x4b6f,0xa570,0x54e4,0xd260,
                        0xe968,0xd520,0xdaa0,0x6aa6,0x56df,0x4ae0,0xa9d4,0xa4d0,0xd150,0xf252,
                        0xd520
        ];

        //返回农历 y年的总天数
        function lYearDays(y) {
            var i, sum = 348;
            for(i=0x8000; i>0x8; i>>=1) sum += (lunarInfo[y-1900] & i)? 1: 0;
            return(sum+leapDays(y));
        };

        //返回农历 y年闰月的天数
        function leapDays(y) {
            if(leapMonth(y)) return( (lunarInfo[y-1899]&0xf)==0xf? 30: 29);
            else return(0);
        };

        //返回农历 y年闰哪个月 1-12 , 没闰返回 0
        function leapMonth(y) {
            var lm = lunarInfo[y-1900] & 0xf;
            return(lm==0xf?0:lm);
        };

        //返回农历 y年m月的总天数
        function monthDays(y,m) {
            return( (lunarInfo[y-1900] & (0x10000>>m))? 30: 29 );
        };

        //计算农历
        //根据参数objDate的公历日期，返回农历日期对象
        function lunar(objDate) {
           var lnYear, lnMonth, lnDay;
           
           var i, leap=0, temp=0;
           var offset = (Date.UTC(objDate.getFullYear(),objDate.getMonth(),objDate.getDate()) - Date.UTC(1900,0,31))/86400000;

           for(i=1900; i<2100 && offset>0; i++) { temp=lYearDays(i); offset-=temp; }

           if(offset<0) { offset+=temp; i--; }

           lnYear = i;

           leap = leapMonth(i); //闰哪个月
           isLeap = false;

           for(i=1; i<13 && offset>0; i++) {
              //闰月
              if(leap>0 && i==(leap+1) && isLeap==false)
                 { --i; isLeap = true; temp = leapDays(lnYear); }
              else
                 { temp = monthDays(lnYear, i); }

              //解除闰月
              if(isLeap==true && i==(leap+1)) isLeap = false;

              offset -= temp;
           }

           if(offset==0 && leap>0 && i==leap+1)
              if(isLeap)
                 { isLeap = false; }
              else
                 { isLeap = true; --i; }

           if(offset<0){ offset += temp; --i; }

           lnMonth = i;
           lnDay = offset + 1;
           
           return new Date(lnYear, lnMonth-1, lnDay); //日期对象
        };
        
        //前面都是前期准备！！！
        //最后一句，得到想要的：农历年生肖
        return sx[(lunar(objDate).getFullYear() - 4) % 12];
    };

    /**
    //测试年份的生肖
    
    function test(){
        //var d = new Date();
        //var d = new Date(2016,10,5); //注意：月份是从0开始的！
        var d = new Date("2016/11/5");
        console.log("公历：");
        console.log(d);

        var f = getSxYear(d);
        console.log("生肖：");
        console.log(f, "年");
    };
    */
    
    //取长度为n的零数组
    function get_zero_list(n){
        var zero_list = [];
        for (var i = 0; i < n; i++){
            zero_list.push(0);
        }
        return zero_list;
    };
        
    //仿python的range函数
    function get_range(start, end, step=1){
        var range = [];
        for (var i = start; i < end; i += step){
            range.push(i);
        }
        return range;
    };
    
    //仿python的random.sample函数
    function get_sample(arr, k){
        var tmp = arr,
            sample = [];
        
        for(var i = 0; i < k; i++){
            ix = parseInt(Math.random() * tmp.length)
            sample.push(tmp[ix]);
            tmp = tmp.slice(0, ix).concat(tmp.slice(ix+1)); //tmp长度减一，注意这里使用切片与拼接，而不是delete!
        }
        
        return sample;
    };
    
    //仿python的zip函数，用于hot指标
    function zip(arr1, arr2){
        if (arr1.length != arr2.length){throw "两个数组长度不一致！";} //抛出错误！
        
        var zip_list = [];
        for(var i = 0; i < arr1.length; i++){
            zip_list.push([arr1[i], arr2[i]])
        }
        return zip_list;
    };
    
    //比较函数，用于数组排序sort
    function cmp(a,b){
        if(a > b){
            return 1;
        }else if(a < b){
            return -1;
        }else{
            return 0;
        }
    };
    
    //比较函数，用于hot指标
    function cmp2(a,b){
        if(a[1]>b[1]){
            return 1;
        }else if(a[1]<b[1]){
            return -1;
        }else{
            return 0;
        }
    };
    
    function get_mod_list(m=2){
        return (m % 2 == 0)?get_range(parseInt(m/2), m):get_range(0, m).filter(function(x){return x%2 != m%2;});
    };
    
    function get_fen_list(f=2){
        return get_range(0, f).filter(function(x){return x%2 != f%2;});
    };
    
    function get_x6_list(){
        //1个位置
        return get_sample(get_range(0, 12), 6).sort(cmp);
    };
    
    function get_bs_list(current_color='r'){
        ix = 'rgb'.indexOf(current_color)
        ix_list = [[1,2],[0,2],[0,1]][ix] //小伎俩，避免从[0,1,2]里删除
        return colors[ix_list[0]].concat(colors[ix].filter(function(x){return x%2==1;})); // 取一波 + 半波单
    };
    
    function get_rnd_list(){
        return get_sample(get_range(1, max_number + 1), parseInt((max_number + 1)/2)).sort(cmp);
    };
    
    function get_a_list(){
        return get_sample(get_range(1, max_number + 1), parseInt((max_number + 1)/2)).sort(cmp);
    };
    
    function get_zx_list(){
        //选7个号：C(49,7)=85.9kk+, C(45,7)=45.3kk+, C(44,7)=38.3kk+
        return get_sample(get_range(1, max_number + 1), 44).sort(cmp);
    };
    
    function get_zxsx_list(){
        //选7个位置的生肖：C(12,7) + 6*C(12,6) + C(12,5)*(C(5,2) + C(5,1)) + C(12,4)*(C(4,3) + 2*C(4,2) + C(4,1)) + C(12,3)*(...)
        return get_sample(get_range(0, 12), 11).sort(cmp);
    };
    

    
    
    /**
     * ==============================
     * 特码 指标函数
     * ==============================
     */
    
    //随机
    function rnd(num, rnd_list){
        return (rnd_list.indexOf(num) > -1)?1:-1;
    };

    //给定
    function in_(num, a_list){
        return (a_list.indexOf(num) > -1)?1:-1;
    };
    
    //模
    function mod(num, m, mod_list){
        return (mod_list.indexOf(num % m) > -1)?1:-1;
    };

    //分
    function fen(num, f, fen_list){
        return (fen_list.indexOf(parseInt(num / ((max_number + 1) / f))) > -1)?1:-1;
    };
    
    //波色
    function bs(num, bs_list){ //静态参数
        // 一波半
        return (bs_list.indexOf(num) > -1)?1:-1;
    };
    
    //六肖
    function x6(num, x6_list){ //静态参数
        return (x6_list.indexOf(num % 12) > -1)?1:-1;
    }
    
    //路数
    function ls(num){
        shi = (parseInt(num / 10) % 10) % 3;
        ge = (num % 10) % 3;
        retrun (shi * ge == 0 && shi + ge != 0)?1:-1 //单零路
    };
    
    //跨度
    function kd(num){
        shi = parseInt(num / 10) % 10;
        ge = num % 10;
        return ([0,4,5,6,7,8,9].indexOf(Math.max(shi, ge) - Math.min(shi, ge)) > -1)?1:-1;
    };
    
    //距离（相对指标）
    function jl(sub){ // 注意参数sub
        return (max_number/4 < math.abs(sub) && math.abs(sub) < 3 * max_number/4)?1:-1;
    };

    //与前差（相对指标）
    function yqc(sub){ // 注意参数sub
        return (sub > 0)?1:-1;
    };

    //前期（相对指标）
    function pre(num, pre_list){
        return (pre_list.indexOf(num) > -1)?1:-1;
    };
    
    //冷热（相对指标）
    function hot(num, pre_list, jiaquan_type){
        // 五种情况：线性加权，泰勒加权，指数加权，计数加权，1-0加权 ['xx', 'tl', 'zs', 'js', 'tf']
        var n = max_number; // 号码个数

        var tmp = get_zero_list(n); // 记录对应位置的权重
        for (var i in pre_list){
            var x = pre_list[i];
            if (jiaquan_type == 'xx'){
                tmp[x-1] += i / get_range(1, n+1).reduce(function(a,b){return a+b;})
            }else if (jiaquan_type == 'tl'){
                tmp[x-1] += 1 / (n- i + 1);
            }else if (jiaquan_type == 'zs'){
                tmp[x-1] += 1 / Math.pow(2, (n - i));
            }else if (jiaquan_type == 'js'){
                tmp[x-1] += 1;
            }else if (jiaquan_type == 'tf'){ //等同于pre
                tmp[x-1] = 1;
            }
        }
        tmp = zip(get_range(1, n+1), tmp);
        tmp.sort(cmp2);
        tmp.reverse();
        var hot_list = [];
        for (var i = 0; i < n; i++){
            hot_list.push(tmp[i][0]);
        }
        hot_list = hot_list.slice(0, parseInt(n/2)); // 找出最热的一半号码
        
        return (hot_list.indexOf(num) > -1)?1:-1;
    };
    
    /**
     * ==============================
     * 平特 指标函数
     * ==============================
     */
    function zxsx(nums, zxsx_list){ // 静态参数
        //'''组选生肖'''
        // 七个位置
        nums.map(function(x){return x%12;}).forEach(function(x){
            if (zxsx_list.indexOf(x) == -1){return 0;}
        })
        return 1;
        //return 1 if set(nums % 12).issubset(set(zxsx_list)) else 0
    }
    
    function zx(nums, zx_list){ // 静态参数
        //'''组选'''
        // 七个位置
        // C(49,7)/2 = C(45,7)-,    C(49,7)/2 = C(44,7)+
        nums.forEach(function(x){
            if (zx_list.indexOf(x) == -1){return 0;}
        })
        return 1;
        //return 1 if set(nums).issubset(set(zx_list)) else 0
    };
    
    /**
     * ==============================
     * 转化函数
     * ==============================
     */
    
    // 根据位置、类型，生成用于计算指标的num，支持一星、二星、及以上!!!
    function get_number_series(){
        //如 loc = '0000001'，则，取 dataframe[6]
        
        return dataframe[loc.indexOf("1")];
    };
    
    //选号（逆向调度）
    function unadapter(zbname, args=[], tf_n=0, dir=1){
        
        return get_range(1, max_number + 1).filter(function(x,args){return zbfuncs[zbname](x,args) == dir;}, args);
    };
    
    
    //调度
    function adapter(loc, zbname, args=[], tf_n=0){
        //zbname 是String类型，如：zbname='mod'
        var series_of_number = get_number_series()
        var series = null;
        
        //['rnd','in_','mod','fen','ls','kd','jl','yqc','pre','hot','bs','x6','zx','zxsx','presx','hotsx']
        if(['mod','fen'].indexOf(zbname) > -1){ 
            series = series_of_number.map(function(x){return zbfuncs[zbname](x, args[0], args[1]);}); // 两个参数
            
        }else if(['rnd','in_','bs','x6'].indexOf(zbname) > -1){
            series = series_of_number.map(function(x){return zbfuncs[zbname](x, args[0]);});  // 一个参数
            
        }else if(['ls','kd'].indexOf(zbname) > -1){
            series = series_of_number.map(function(x){return zbfuncs[zbname](x);});  // 零个参数
            
        }else if(['jl', 'yqc'].indexOf(zbname) > -1){
            //方式一
            //var zip_list = zip(series_of_number, get_zero_list(pre_n).concat(series_of_number.slice(0, series_of_number.length - pre_n)));
            //series = zip_list.map(function(x){return zbfuncs[zbname](x[0] - x[1]);})
            
            //方式二
            series = series_of_number.map(function(x, i, s){return zbfuncs[zbname](x - s[i-pre_n]);}); //前pre_n个 NaN
            
        }else if(['pre'].indexOf(zbname) > -1){
            series = series_of_number.map(function(x, i, s){return zbfuncs[zbname](x, s.slice(i-max_number, i));}); //前49个 0(-1)
            
        }else if(['hot'].indexOf(zbname) > -1){
            series = series_of_number.map(function(x, i, s){return zbfuncs[zbname](x, s.slice(i-max_number, i), args[0]);}); //前49个 0(-1)
            
        }else if(['zxsx', 'zx'].indexOf(zbname) > -1){
            series = dataframe.map(function(x){return zbfuncs[zbname](x, args[0]);});  // 一个参数，但是，注意差别：dataframe
            
        }else if(['presx','hotsx'].indexOf(zbname) > -1){
        
        }
        
        //var series = series_of_number.map(function(x){return zbfuncs[zbname](x, args);})
        
        if(tf_n == 0){
            return series;
        }else{
            return tf(series);
        }
    };
    
    //同反
    function tf(series, tf_n=1){
        //使用了数组切片、拼接、zip、map
        return zip(series, get_zero_list(tf_n).concat(series.slice(0, series.length-tf_n))).map(function(x){return x[0]-x[1]==0?1:-1;})
    }
    
    /**
     * ==============================
     * K线函数
     * ==============================
     */
    
    //仿python的numpy.cumsum函数
    function cumsum(series){
        var close = series.map(function(x, i, s){return s.slice(0,i+1).reduce(function(a,b){return a+b;})});
        
        //var close = [];
        //for (var i=0; i < series.length; i++){
        //    close.push(series.slice(0,i+1).reduce(function(a,b){return a+b;}));
        //}
        return close;
    };
    
    //仿python的talib.MA函数
    function ma(close, timeperiod=5){
        var arr, avr, ma_list;
        
        ma_list = get_zero_list(timeperiod-1); //粗暴地置前11个为0
        for (var i = timeperiod-1; i < close.length; i++){
            arr = close.slice(i+1-timeperiod, i+1)
            
            avr = arr.reduce(function(a,b){return a+b;}) / timeperiod; //均值
            ma_list.push(avr);
        }
        return ma_list;
    };
    
    //仿python的talib.STDDEV函数
    function stddev(close, timeperiod=5){
        var arr, avr, var_, std_list;
        
        std_list = get_zero_list(timeperiod-1); //粗暴地置前4个为0
        for (var i = timeperiod-1; i < close.length; i++){
            arr = close.slice(i+1-timeperiod, i+1)
            
            avr = arr.reduce(function(a,b){return a+b;}) / timeperiod; //均值
            var_ = arr.map(function(x){return (x-avr)*(x-avr);}).reduce(function(a,b){return a+b;}) / timeperiod; //方差
            
            std_list.push(Math.sqrt(var_)); //标准差
        }
        return std_list;
        
    };
    
    //仿python的talib.BBANDS函数
    function bbands(close, timeperiod=5){
        var ma_list, std_list, zip_list, bbands_list=[];
        
        ma_list = ma(close, timeperiod);
        std_list = stddev(close, timeperiod);
        zip_list = zip(ma_list, std_list);
        
        bbands_list[0] = zip_list.map(function(x){return x[0]+2*x[1];});
        bbands_list[1] = zip_list.map(function(x){return x[0]+x[1];});
        bbands_list[2] = ma_list;
        bbands_list[3] = zip_list.map(function(x){return x[0]-x[1];});
        bbands_list[4] = zip_list.map(function(x){return x[0]-2*x[1];});
        
        return bbands_list;
    };
    
    //仿python的talib.STOCHRSI函数
    //fastk, fastd = ta.STOCHRSI(close, timeperiod=14, fastk_period=10, fastd_period=5, fastd_matype=0)
    
    //仿python的numpy.cumsum函数
    
    //布林通道宽度
    function bands_width(close, timeperiod=5){
        return stddev(close, timeperiod);
    };
    
    //相对走势
    function xiangdui_zoushi(close, timeperiod=5){
        return zip(close, ma(close, timeperiod)).map(function(x){return x[0]-x[1];});
    };
    
    //趋势
    function trend(close, timeperiod=5){
        var ma_list = ma(close, timeperiod);
        var diff_ma = zip(ma_list, [0].concat(ma_list.slice(0, ma_list.length))).map(function(x){return x[0]-x[1];});
        
        var trend_list = diff_ma.map(function(x){return Math.sign(x);})
        return trend_list;
    };
    
    //均线斜率（差分）
    function ma_slope(close, timeperiod=5){
        var ma_list = ma(close, timeperiod);
        var diff_ma = zip(ma_list, [0].concat(ma_list.slice(0, ma_list.length))).map(function(x){return x[0]-x[1];});
        return diff_ma;
    };
    
    /** 
     * ==============================
     * 策略函数
     * ==============================
     */
    
    function get_dataframe(){
        return dataframe;
    };
    
    //下面三个函数用于判断号码波色
    function is_red(num){
        return colors[0].indexOf(num) > -1;
    };
    
    function is_green(num){
        return colors[1].indexOf(num) > -1;
    };
    
    function is_blue(num){
        return colors[2].indexOf(num) > -1;
    };
    //生成连续200个日期标签，仅用于测试！
    function get_200_labels(n=200){
        var d = new Date();
        var labels = get_range(0,n).map(function(x){var nd = new Date(d-x*86400000); return nd.toLocaleDateString();})
        labels.reverse();
        return labels;
    }
    
    return {
        get_200_labels: get_200_labels,
        
        is_blue: is_blue,
        is_green: is_green,
        is_red: is_red,
        
        //dataframe: dataframe,
        get_dataframe: get_dataframe,
        get_number_series: get_number_series,
        
        get_zero_list: get_zero_list,
        get_range: get_range,
        get_sample: get_sample,
        zip: zip,
        cmp: cmp,
        cmp2: cmp2,
        
        get_mod_list: get_mod_list,
        get_fen_list: get_fen_list,
        get_x6_list: get_x6_list,
        get_bs_list: get_bs_list,
        get_rnd_list: get_rnd_list,
        get_a_list: get_a_list,
        get_zx_list: get_zx_list,
        get_zxsx_list: get_zxsx_list,
        
        
        load_data: load_data,
        load_data2: load_data2,
        update_data: update_data,
        
        unadapter: unadapter,
        
        adapter: adapter,
        cumsum: cumsum,
        
        ma: ma,
        stddev: stddev,
        bbands: bbands,
        bands_width: bands_width,
        xiangdui_zoushi: xiangdui_zoushi,
        ma_slope: ma_slope
    };
}());