#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tickets viewer on cmd

Usage:
	tickets [-gdtkz] <from> <to> <date>

Options:
	-h,--help 		显示帮助栏
	-g 			高铁
	-d 			动车
	-t 			特快
	-k 			快速
	-z 			直达

Example:
	tickets 北京 上海 2016-10-10
	tickets -dg 成都 南京 2016-10-10
"""
from docopt import docopt
from prettytable import PrettyTable
from stations import stations
from colorama import init,Fore
import json
import requests

init()

class TrainsCollections(object):
	header='车次 车站 时间 历时 一等 二等 软卧 硬卧 硬座 无座'.split()

	def __init__(self,avaliable_trains,options) :
		"""建立一个TrainsCOllections类用于存放可选的火车班次
		:param available_trains:包含所有可选列车的列表，每个元素由字典构成，包含车次的车次号、出发时间、到站时间等等
		:param options:查询的选项，-g表示高铁等等
		
		"""
		self.avaliable_trains=avaliable_trains
		self.options=options
	def _get_duration_(self,raw_train) :
		
		'''
		不用考虑天数，因为火车时间最大单位是小时...
		init_duration=raw_train.get('lishi')
		if init_duration.count(':')==2 :
			duration=init_duration.replace(':','天',1).replace(':','小时')+'分'
		else :
			duration=raw_train.get('lishi').replace(':','小时')+'分'
		'''
		#获取火车行驶时间并格式化字符串
		duration=raw_train.get('lishi').replace(':','小时')+'分'
		#判断行驶时间是否已"00"开始，若如此，只返回分钟
		if duration.startswith('00') :
			return duration[4:]
		#以'0'开始，返回所有字符
		if duration.startswith('0') :
			return duration[1:]
		return duration
	#获取符合查询要求的车次，将基本信息写入一个list
	seat_order=['M','O','A4','A3','A1','WZ']
	#read_only_attribute_'trains'
	@property
	def trains(self) :
		for init_raw_train in self.avaliable_trains:
			raw_train=init_raw_train['queryLeftNewDTO']
			#这些字典的key得通过返回的json确定名称才能得到正确的车次字典
			train_no=raw_train['station_train_code']
			#获取车次
			train_price_no=raw_train['train_no']
			initial=train_no[0].lower()#小写以与用户输入的options比较
			#这里not self.options or initial in self.options
			#顺序是先not self.options判断用户输入的是否为空指令串，是就为True，就打印本趟列车，肯定符合（没有要求）。不是就为False,然后看本趟列车代码是否在用户要求之中
			if not self.options or initial in self.options:
				price_url = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no={}&from_station_no={}&to_station_no={}&seat_types={}&train_date={}'.format(
					raw_train['train_no'], raw_train['from_station_no'], raw_train['to_station_no'],
					raw_train['seat_types'], self.parse_train_date(raw_train['start_train_date'])
				)
				price_request = requests.get(price_url, verify=False)
				price_data = price_request.json()
				print(price_data)
				price_json=price_data['data']
				train =[
					train_no,
					'\n'.join([Fore.GREEN+raw_train['from_station_name']+Fore.RESET,
						Fore.RED+raw_train['to_station_name']+Fore.RESET]),
					'\n'.join([Fore.GREEN+raw_train['start_time']+Fore.RESET,
						Fore.RED+raw_train['arrive_time']+Fore.RESET]),
					self._get_duration_(raw_train),
					raw_train['zy_num'],
					raw_train['ze_num'],
					raw_train['rw_num'],
					raw_train['yw_num'],
					raw_train['yz_num'],
					raw_train['wz_num']
				]
				if price_request.status_code==200 :
					print(train_no)#打印那辆列车出了问题
					for i in range(4,10) :
						if train[i] == '--' or train[i]=='无' :
							pass
						else:
							train[i]='\n'.join([train[i],price_json[self.seat_order[i-4]]])
				yield train
	def prettyprint(self) :
		pt=PrettyTable()
		pt._set_field_names(self.header)
		for train in self.trains :
			pt.add_row(train)
		print(pt)
	def parse_train_date(self,train_date) :
		a=[train_date[0:4],train_date[4:6],train_date[6:]]
		return '-'.join(a)
def cli():
	"""command-line interface"""
	arguments=docopt(__doc__)
	from_station=stations.get(arguments['<from>'])
	to_station=stations.get(arguments['<to>'])
	train_date=arguments['<date>']
	url='https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(
		train_date,from_station,to_station
		)
	options=''.join([key for key,value in arguments.items() if value is True])
	r=requests.get(url,verify=False)
	available_trains=r.json()['data']
	TrainsCollections(available_trains,options).prettyprint()
	
	

if __name__ == '__main__':
	cli()
