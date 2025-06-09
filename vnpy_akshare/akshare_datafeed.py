import akshare as ak
from datetime import datetime 
from typing import List, Optional, Callable
import pandas as pd
import pytz
from time import sleep

from vnpy.trader.constant import Exchange, Interval, Product
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.utility import round_to
from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.setting import SETTINGS

EXCHANGE_MAP = {
    Exchange.SSE: "sh",
    Exchange.SZSE: "sz",
}

INTERVAL_MAP = {
    Interval.MINUTE: "1",
    Interval.HOUR: "60",
    Interval.DAILY: "daily",     # 改为 daily
    Interval.WEEKLY: "weekly",   # 改为 weekly
}

# 设置中国时区
CHINA_TZ = pytz.timezone("Asia/Shanghai")

def to_datetime(timestamp: str) -> datetime:
    """将时间戳字符串转换为datetime对象"""
    dt = pd.to_datetime(timestamp).to_pydatetime()
    if not dt.tzinfo:
        dt = CHINA_TZ.localize(dt)
    return dt

class Datafeed(BaseDatafeed):
    """AKShare数据服务接口"""
    
    def __init__(self):
        """构造函数"""
        self.inited: bool = False
        self.api = None
    
    def init(self, output: Callable = print) -> bool:
        """初始化"""
        if self.inited:
            return True
        
        # 不需要初始化，直接返回成功
        self.inited = True
        return True
    
    def query_bar_history(
        self, 
        req: HistoryRequest, 
        output: Callable = print
    ) -> Optional[List[BarData]]:
        """查询K线数据"""
        if not self.inited:
            n: bool = self.init(output)
            if not n:
                return None
            
        symbol: str = req.symbol
        exchange: Exchange = req.exchange
        interval: Interval = req.interval
        start: datetime = req.start
        end: datetime = req.end
        
        # 将交易所代码转换为akshare格式
        exchange_str = EXCHANGE_MAP.get(exchange, "")
        if not exchange_str:
            output(f"不支持的交易所: {exchange}")
            return None
            
        # 将K线周期转换为akshare格式
        interval_str = INTERVAL_MAP.get(interval, "")
        if not interval_str:
            output(f"不支持的K线周期: {interval}")
            return None
            
        # 获取数据
        df = None
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # 判断是否为ETF
                is_etf = symbol.startswith(("51", "15"))
                
                if is_etf:
                    # ETF数据
                    if interval == Interval.MINUTE:
                        # ETF分钟数据 限量: 单次返回指定 ETF、频率、复权调整和时间区间的分时数据, 其中 1 分钟数据只返回近 5 个交易日数据且不复权
                        df = ak.fund_etf_hist_min_em(
                            symbol=symbol,
                            period=interval_str,
                            start_date=start.strftime("%Y%m%d"),
                            end_date=end.strftime("%Y%m%d")
                        )
                    else:
                        # ETF日线数据
                        df = ak.fund_etf_hist_em(
                            symbol=symbol,
                            period=interval_str,
                            start_date=start.strftime("%Y%m%d"),
                            end_date=end.strftime("%Y%m%d"),
                            adjust="qfq"
                        )
                else:
                    # 股票数据
                    if interval == Interval.MINUTE:
                        # 分钟级数据 限量: 单次返回指定股票、频率、复权调整和时间区间的分时数据, 其中 1 分钟数据只返回近 5 个交易日数据且不复权
                        df = ak.stock_zh_a_hist_min_em(
                            symbol=symbol,
                            period=interval_str,
                            start_date=start.strftime("%Y%m%d"),
                            end_date=end.strftime("%Y%m%d")
                        )
                    else:
                        # 日线及以上周期数据
                        df = ak.stock_zh_a_hist(
                            symbol=symbol,
                            period=interval_str,
                            start_date=start.strftime("%Y%m%d"),
                            end_date=end.strftime("%Y%m%d"),
                            adjust="qfq"
                        )
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    output(f"获取K线数据失败，正在进行第{retry_count}次重试: {e}")
                    sleep(2)  # 等待2秒后重试
                else:
                    output(f"获取K线数据失败，已达到最大重试次数: {e}")
                    return None
        
        if df is None or df.empty:
            output("获取的数据为空")
            return None
            
        try:
            # 根据时间周期确定时间列名
            time_column = "时间" if interval == Interval.MINUTE else "日期"

            # 重命名列以匹配数据格式
            df = df.rename(columns={
                time_column: "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
            })
            
            # 设置日期为索引
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
                
        except Exception as e:
            output(f"处理数据失败: {e}")
            return None
            
        # 数据转换
        bars: List[BarData] = []
        
        if df is not None and not df.empty:
            for ix, row in df.iterrows():
                # 将 Timestamp 转换为 datetime 并添加时区信息
                dt = ix.to_pydatetime()
                if interval == Interval.DAILY:
                    # 对于日线数据，设置时间为收盘时间 15:00:00
                    dt = dt.replace(hour=15, minute=0, second=0)
                dt = CHINA_TZ.localize(dt)
                
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=interval,
                    volume=float(row["volume"]),
                    turnover=float(row["amount"]),
                    open_price=float(row["open"]),
                    high_price=float(row["high"]),
                    low_price=float(row["low"]),
                    close_price=float(row["close"]),
                    gateway_name="AKSHARE"
                )
                bars.append(bar)
        
        return bars
