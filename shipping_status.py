import asyncio
import math
from asyncio import Semaphore
import aiohttp


async def get_tracking_status(shipping_number_list: list):
    """
    获取运输信息
    shipping_number_list: -> 运输号列表
        type: list
    return:
        [{
            send_country -> 发送国家
            receive_country -> 接收国家
            tracking_detail: -> 运输详情
                track_date -> 运输时间戳
                location -> 货物所在位置
                content -> 详情
                sort_num -> 索引(排序用)
            tracking_number -> 运输单号
            status: -> 运输状态
                notfound -> 未查询到
                transit -> 运输途中
                pickup -> 到达待取
                undelivered -> 投递失败
                delivered -> 已签收
                exception -> 可能异常
                expired -> 运输过久
            shipping_day -> 运输时间
            logistics -> 物流商
        }]
    """
    link = 'https://ext.trackdog.com/ajaxTrack.json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Referer'   : "https://www.baidu.com",
    }
    total = 40
    item_list = []
    shipping_number_list = list(set(shipping_number_list))  # 去重，不去重会报错
    for shipping_number in shipping_number_list:
        item = {"trackNum": shipping_number, "code": '', "pf": '', "pf_c": ''}  # 构建请求体
        item_list.append(item)
    page_num = math.ceil(len(item_list) / total)
    semaphore = Semaphore(page_num)  # 并发信号量

    async def get_data(data, count=1):
        if count >= 5:  # 重试，5次以上，返回空列表
            return []
        async with semaphore:
            try:
                re_data = []
                async with session.post(link, json=data, verify_ssl=False, headers=headers) as resp:
                    json_data = await resp.json()
                    for j_data in json_data['data']:
                        j_item = {
                            'send_country'   : j_data['sendCountryCn'],
                            'receive_country': j_data['receiveCountryCn'],
                            'tracking_detail': [],
                            'tracking_number': j_data['trackingNumber'],
                            'logistics'      : j_data['sendLogistics'],
                            'shipping_day'   : j_data['shippingDay'],
                            'status'         : j_data['status']
                        }
                        detail_list = j_data['sendTrackingDetail']
                        for detail in detail_list:
                            detail_item = {
                                'track_date': detail['trackDate'],
                                'location'  : detail['location'],
                                'content'   : detail['content'],
                                'sort_num'  : detail['sortNum']
                            }
                            j_item['tracking_detail'].append(detail_item)
                        re_data.append(j_item)
                return re_data
            except Exception as e:
                count += 1
                return await get_data(data, count)

    async with aiohttp.ClientSession() as session:
        scrape_index_tasks = [asyncio.ensure_future(get_data(item_list[(i * total): (i * total) + total])) for i in range(page_num)]
        result_list = await asyncio.gather(*scrape_index_tasks)
        return result_list


if __name__ == '__main__':
    shipping_list = ['YT2020321272051744', 'YT2020521272027165', 'YT2020321272051709']
    res = asyncio.run(get_tracking_status(shipping_list))
    for i in res:
        print(i)
