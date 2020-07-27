import asyncio
import math
import re
from asyncio import Semaphore

import aiohttp
import execjs
from aiohttp import ClientConnectorError
from lxml import etree


def get_tr_list(html):
    """
    获取订单页tr列表
    """
    item_data_list = []
    html = etree.HTML(html)
    tr_list = html.xpath('//tbody[@class="xianshishujudate"]/tr[@class="goodsId "]')
    for j, tr in enumerate(tr_list):
        a_list = [tr]
        for i in range(1, 10):
            sibling = tr.xpath(f'following-sibling::tr[{i}][@class="goodsId "]')
            if sibling:
                break
            else:
                sibling = tr.xpath(f'following-sibling::tr[{i}]')
                if sibling:
                    a_list += sibling
                else:
                    break
        item_data_list.append(a_list)
    return item_data_list


def parse_tr(tr_list):
    """
    解析每个tr中的数据
    """
    # 第一个tr
    tr1 = tr_list[0].xpath("./td[1]")
    aa = ['包裹号', '交易号', '拣货备注', '订单备注', '买家指定', '平台渠道', '店铺账号', '订单状态', '拣货单打印时间', '面单打印时间', '物流方式', '物流单号', '退款状态']
    if tr1:
        包裹号 = tr1[0].xpath('./a/text()')
        交易号 = tr1[0].xpath('./input[1]/@value')
        订单备注 = tr1[0].xpath('./span[@class="squareSpan hover-prompt hoverPrompt"]/@data-content')
        拣货备注 = tr1[0].xpath('./span[@class="squareSpan dataTriggerHover"]/@data-content')
        if 订单备注:
            订单备注 = re.findall("padding-left:5px;'>(.*?)</td>", 订单备注[0])
    买家指定 = tr_list[0].xpath('./td[3]/div/text()')
    平台店铺 = tr_list[0].xpath('./td[4]/span/text()')
    物流方式 = tr_list[1].xpath('./td[6]/span/text()')
    物流单号 = tr_list[1].xpath('./td[6]/p//a/text()')
    面单打印时间 = tr_list[1].xpath('./td[7]/p/span[2]/@title')
    拣货单打印时间 = tr_list[1].xpath('./td[7]/p/span[1]/@title')
    订单状态 = tr_list[1].xpath('./td[7]/text()')
    退款状态 = tr_list[1].xpath('./td[7]/span/text()')
    if 买家指定:
        买家指定 = 买家指定[0][6:]
    if 平台店铺:
        if '：' in 平台店铺[0]:
            平台渠道, 店铺账号 = 平台店铺[0][1:-1].split("：")
        else:
            平台渠道, 店铺账号 = [平台店铺[0][1:-1]], ''
    if 退款状态:
        退款状态 = 退款状态[0][1:-1]
    # 第二至多个个tr, 下面的都可能为多个，所以用列表存储
    tr_data = {'SKU' : [], '图片网址': [], '来源URL': [], '产品数量': [], '币种金额': [],
               '产品规格': [], '销售链接': [], '订单金额': [], '订单号': [],
               '下单时间': [], '付款时间': [], '提交时间': [], '发货时间': [], '退款时间': [], '剩余发货天数': []
               }
    for tr in tr_list[1:]:
        图片网址 = tr.xpath('./td[1]//img/@data-order')
        销售链接 = tr.xpath('./td[1]//td[2]//a/@href')
        SKU = tr.xpath('./td[1]//td[2]//a/text()')
        产品数量 = tr.xpath('./td[1]//span[@class="circularSpanRed"]/text()')
        币种金额 = tr.xpath('./td[1]//p[2]/text()')  # 币种/产品售价
        来源URL = tr.xpath('./td[1]/li[@role="presentation"]/a/@data-url')
        产品规格 = tr.xpath('./td[1]//span[@class="isOverLengThHide"]/text()')
        订单金额 = tr.xpath('./td[2]/text()')
        订单号 = tr.xpath('./td[4]//a/text()')
        时间 = tr.xpath('./td[5]/text()')
        剩余发货天数 = tr.xpath('./td[5]/span')
        if 剩余发货天数:
            剩余发货天数 = 剩余发货天数[0].xpath('string()')
            剩余发货天数 = 剩余发货天数.split(',')
            剩余发货天数 = js.call('getTimerString', eval(剩余发货天数[1]), 剩余发货天数[2].strip()[1:-3])
        tr_data['SKU'].append(SKU)
        tr_data['图片网址'].append(图片网址)
        tr_data['销售链接'].append(销售链接)
        tr_data['来源URL'].append(来源URL)
        tr_data['产品数量'].append(产品数量)
        tr_data['币种金额'].append(币种金额)
        tr_data['产品规格'].append([i.strip() for i in 产品规格])
        tr_data['订单金额'].append([订单金额[0].strip()])
        tr_data['订单号'].append(订单号)
        tr_data['剩余发货天数'].append(剩余发货天数)
        for i in 时间:
            if '下单' in i:
                tr_data['下单时间'].append([i.strip()[3:]])
            if '付款' in i:
                tr_data['付款时间'].append([i.strip()[3:]])
            if '提交' in i:
                tr_data['提交时间'].append([i.strip()[3:]])
            if '发货' in i:
                tr_data['发货时间'].append([i.strip()[3:]])
            if '退款' in i:
                tr_data['退款时间'].append([i.strip()[3:]])
    item = {}
    for i in aa:
        j = eval(i)
        if j:
            if type(j) == str:
                item[i] = j.strip()
            else:
                item[i] = j[0].strip()
        else:
            item[i] = ''
    item['detail'] = tr_data
    return item


def parse_detail(html):
    """
    解析详情页
    """
    item = {}
    html = html.replace('\n', '').replace('\t', '')
    item['包裹号'] = re.findall('<span id="dxmPackageNumDetailSpan">(.*?)</span>', html)
    item['买家账号'] = re.findall('买家：(.*?)</div>', html)
    item['买家姓名'] = re.findall('买家姓名/邮箱：(.*?)/<span id="buyerEmailSpan">', html)
    item['买家Email'] = re.findall('/<span id="buyerEmailSpan">(.*?)</span></div>', html)
    item['收件人姓名'] = re.findall('id="detailContact1">(.*?)</div>', html)
    item['收件人公司'] = re.findall('id="companyName1">(.*?)</div>', html)
    item['收件人税号'] = re.findall('id="taxNumber1">(.*?)</div>', html)
    item['收件人门牌号'] = re.findall('id="apartmentNumber1">(.*?)</div>', html)
    item['地址1'] = re.findall('id="detailAddr11">(.*?)</div>', html)
    item['地址2'] = re.findall('id="detailAddress21">(.*?)</div>', html)
    item['收件人城市'] = re.findall('id="detailCity1">(.*?)</div>', html)
    item['洲'] = re.findall('id="detailProvince1">(.*?)</div>', html)
    item['邮编'] = re.findall('id="detailZip1">(.*?)</div>', html)
    item['收货人电话'] = re.findall('id="detailPhone1">(.*?)</div>', html)
    item['收货人手机'] = re.findall('id="detailMobile1">(.*?)</div>', html)
    item['中文报关名'] = re.findall('class="nameChSpan">(.*?)</span>', html)
    item['英文报关名'] = re.findall('class="nameEnSpan">(.*?)</span>', html)
    item['英文报关名'] = re.findall('class="nameEnSpan">(.*?)</span>', html)
    item['申报价格单位'] = re.findall('(.)<span class="deValSpan">', html)
    item['申报价格'] = re.findall('<span class="deValSpan">(.*?)</span>', html)
    item['报关重量单位'] = re.findall('</span>（(.*?)）<span class="hsCodeSpan">', html)
    item['报关重量'] = re.findall('<span class="weightSpan">(.*?)</span>', html)
    发货仓库 = re.findall('<span id="orderPackageStockSpan"></span>(.*?)</td></tr>', html)
    if 发货仓库:
        if 'select' in 发货仓库[0]:
            item['发货仓库'] = ''
        else:
            item['发货仓库'] = 发货仓库
    收货人国家 = re.findall('id="detailCountry1" name11=".*?">(.*?)</div>', html)
    if 收货人国家:
        收货人国家 = 收货人国家[0].split('（')
        item['收货人国家'], item['中文国家名'] = 收货人国家[0], 收货人国家[1][:-1]
    else:
        item['收货人国家'], item['中文国家名'] = '', ''

    for k, v in item.items():
        if type(v) == list:
            if len(v) != 0:
                if len(v) == 1:
                    item[k] = v[0]
                else:
                    item[k] = v
            else:
                item[k] = ''
    return item


def parse_other_data(html):
    xp = etree.HTML(html)
    table = xp.xpath("//table[@id='moneyCny']/tbody")[0]
    包裹号_列表 = table.xpath("./tr[@class='content']/td[2]")
    运费_列表 = table.xpath("./tr[@class='content']/td[8]")
    退款金额_列表 = table.xpath("./tr[@class='content']/td[10]")
    利润_列表 = table.xpath("./tr[@class='content']/td[12]")
    成本利润率_列表 = table.xpath("./tr[@class='content']/td[13]")
    销售利润率_列表 = table.xpath("./tr[@class='content']/td[14]")
    称重重量_列表 = table.xpath("./tr[@class='content']/td[16]")
    items = {}
    for i, v in enumerate(包裹号_列表):
        v = v.xpath('string()').strip()
        items[v] = {
            '运费'   : 运费_列表[i].xpath('string()').strip(),
            '退款金额' : 退款金额_列表[i].xpath('string()').strip(),
            '利润'   : 利润_列表[i].xpath('string()').strip(),
            '成本利润率': 成本利润率_列表[i].xpath('string()').strip(),
            '销售利润率': 销售利润率_列表[i].xpath('string()').strip(),
            '称重重量' : 称重重量_列表[i].xpath('string()').strip(),
        }
    return items


class DxmData:
    def __init__(self, session, cookie):
        self.session = session  # 全局session
        self.data = []  # 最后得到的数据会存在里面，存的是每页的所以数据，例如：[[第一页数据],[第二页数据]]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Cookie'    : cookie,
            'Host'      : 'www.dianxiaomi.com',
            'Origin'    : 'https://www.dianxiaomi.com',
            'Referer'   : 'https://www.dianxiaomi.com/order/index.htm',
        }
        self.html_list = []  # 分页得到的html代码

    async def request_html(self, link, method="post", count=1, **kwargs):
        """
        请求数据，返回的是text（html源代码），不是二进制
        """
        if count >= 5:  # 超时重试次数
            return ''
        try:
            if method == 'post':
                async with self.session.post(link, headers=self.headers, verify_ssl=False, **kwargs) as resp:
                    return await resp.text()
            elif method == 'get':
                async with self.session.get(link, headers=self.headers, verify_ssl=False, **kwargs) as resp:
                    return await resp.text()
        except ClientConnectorError:
            return await self.request_html(link, method="post", count=1, **kwargs)

    async def get_html_list(self):
        """
        获取分页html
        """
        link = 'https://www.dianxiaomi.com/package/list.htm'
        params = {
            'pageNo'         : 1,
            'pageSize'       : 300,
            'shopId'         : -1,
            'isSearch'       : 1,
            'searchType'     : 'orderId',
            'authId'         : -1,
            'orderField'     : 'order_create_time',
            'isVoided'       : -1,
            'isRemoved'      : -1,
            'ruleId'         : -1,
            'printJh'        : -1,
            'printMd'        : -1,
            'jhComment'      : -1,
            'isOversea'      : -1,
            'state'          : '',
            'isFree'         : -1,
            'isBatch'        : -1,
            'custom'         : -1,
            'forbiddenStatus': -1,
            'behindTrack'    : -1,
        }
        html = await self.request_html(link, method='get', params=params)
        total = re.findall('"totalSize" type="hidden" value="(\d+)">', html)  # 获取总共多少条数据，以便分页用
        self.html_list.append(html)
        if total:
            total = int(total[0])
            page_size = math.ceil(total / 300)
            for page in range(2, page_size + 1):
                params.update({'pageNo': page})
                html = await self.request_html(link, method='get', params=params)
                self.html_list.append(html)

    async def get_other_data(self):
        """
        获取利润相关数据，这个可以直接获取非常多数据，改日期和改pageSize就可以了，不用分页
        """
        link = 'https://www.dianxiaomi.com/stat/order/count/profit.htm'
        params = {
            'shopIds'  : '',
            'sortType' : 'otherFeeUsd',
            'pageNo'   : 1,
            'pageSize' : 100000,
            'beginDate': '2010-01-01',
            'endDate'  : '2099-12-30',
        }
        html = await self.request_html(link, method='get', params=params)
        # for 包裹号 in 包裹号_list:
        return parse_other_data(html)

    async def get_detail(self, package_id, index):
        """
        获取订单详情页数据
        """
        link = 'https://www.dianxiaomi.com/package/detail.htm'
        data = {
            'packageId': package_id,
            'history'  : ''
        }
        html = await self.request_html(link, data=data)
        result = parse_detail(html)
        result['index'] = index
        return result

    async def get_data(self):
        """
        获取数据总和
        """
        for html in self.html_list:
            tr_list = get_tr_list(html)
            data_list = []
            for tr__list in tr_list:
                data = parse_tr(tr__list)
                data_list.append(data)
            scrape_index_tasks = [asyncio.ensure_future(self.get_detail(item['交易号'], index)) for index, item in enumerate(data_list)]
            result_list = await asyncio.gather(*scrape_index_tasks)
            other_data = await self.get_other_data()
            for i in result_list:
                index = i.pop('index')
                data_list[index].update(i)
            for i in data_list:
                if other_data.get(i['包裹号']):
                    i.update(other_data[i['包裹号']])
            self.data.append(data_list)


async def main():
    # 一个店铺对应一个cookie
    cookie_list = ['']
    for cookie in cookie_list:
        async with aiohttp.ClientSession() as session:
            dxm = DxmData(session=session, cookie=cookie)
            await dxm.get_html_list()
            await dxm.get_data()
            for i in dxm.data:
                for j in i:
                    print(j)
                print('-' * 100)


if __name__ == '__main__':
    semaphore = Semaphore(100)  # 并发信号量
    js = execjs.compile(open('a.js').read())  # 由于店小秘的发货时间是动态生成的，所以需要引用它相关的js代码
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
