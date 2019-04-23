import sys
from configloader import ConfigLoader
import hashlib
import time
import requests
import base64
import aiohttp
import asyncio
import random
import json
try:
    from PIL import Image
except ImportError:
    Image = None
from io import BytesIO


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)


def randomint():
    return ''.join(str(random.randint(0, 9)) for _ in range(17))


def cnn_captcha(content):
    img = base64.b64encode(content)
    url = "http://47.95.255.188:5000/code"
    data = {"image": img}
    rsp = requests.post(url, data=data)
    captcha = rsp.text
    print(f'此次登录出现验证码,识别结果为{captcha}')
    return captcha
 
       
def input_captcha(content):
    if Image is not None:
        img = Image.open(BytesIO(content))
        # img.thumbnail(size)
        img.show()
        captcha = input('手动输入验证码')
    else:
        captcha = input('您并没有安装pillow模块，但仍然选择了手动输入，那就输呀:')
    return captcha


base_url = 'https://api.live.bilibili.com'


class bilibili():
    __slots__ = ('dic_bilibili', 'var_bili_session', 'app_params', 'var_other_session', 'var_login_session')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(bilibili, cls).__new__(cls, *args, **kw)
            cls.instance.dic_bilibili = ConfigLoader().dic_bilibili
            dic_bilibili = ConfigLoader().dic_bilibili
            cls.instance.var_bili_session = None
            cls.instance.var_other_session = None
            cls.instance.var_login_session = None
            cls.instance.app_params = f'actionKey={dic_bilibili["actionKey"]}&appkey={dic_bilibili["appkey"]}&build={dic_bilibili["build"]}&device={dic_bilibili["device"]}&mobi_app={dic_bilibili["mobi_app"]}&platform={dic_bilibili["platform"]}'
        return cls.instance

    @property
    def bili_session(self):
        if self.var_bili_session is None:
            self.var_bili_session = aiohttp.ClientSession()
            # print(0)
        return self.var_bili_session
        
    @property
    def other_session(self):
        if self.var_other_session is None:
            self.var_other_session = aiohttp.ClientSession()
            # print(0)
        return self.var_other_session
        
    @property
    def login_session(self):
        if self.var_login_session is None:
            self.var_login_session = requests.Session()
            # print(0)
        return self.var_login_session

    def calc_sign(self, str):
        str = f'{str}{self.dic_bilibili["app_secret"]}'
        sign = hashlib.md5(str.encode('utf-8')).hexdigest()
        return sign

    @staticmethod
    def load_session(dic):
        # print(dic)
        inst = bilibili.instance
        for i in dic.keys():
            inst.dic_bilibili[i] = dic[i]
            if i == 'cookie':
                inst.dic_bilibili['pcheaders']['cookie'] = dic[i]
                inst.dic_bilibili['appheaders']['cookie'] = dic[i]
                
    def login_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                # print(self.login_session.cookies, url)
                rsp = self.login_session.post(url, headers=headers, data=data, params=params)
                if rsp.status_code == requests.codes.ok and rsp.content:
                    return rsp
                elif rsp.status_code == 403:
                    print('403频繁')
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
    
    def login_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                # print(self.login_session.cookies, url)
                rsp = self.login_session.get(url, headers=headers, data=data, params=params)
                if rsp.status_code == requests.codes.ok and rsp.content:
                    return rsp
                elif rsp.status_code == 403:
                    print('403频繁')
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def get_json_rsp(self, rsp, url):
        if rsp.status == 200:
            # json_rsp = await rsp.json(content_type=None)
            data = await rsp.read()
            json_rsp = json.loads(data)
            if isinstance(json_rsp, dict) and 'code' in json_rsp:
                code = json_rsp['code']
                if code == 1024:
                    print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                    await asyncio.sleep(1.5)
                    return None
                elif code == 3:
                    print('api错误，稍后重试，请反馈给作者')
                    print(json_rsp)
                    await asyncio.sleep(1)
                    return 3
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
        
    async def get_text_rsp(self, rsp, url):
        if rsp.status == 200:
            return await rsp.text()
        elif rsp.status == 403:
            print('403频繁', url)
        return None

    async def bili_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_session.post(url, headers=headers, data=data, params=params) as rsp:
                    json_rsp = await self.get_json_rsp(rsp, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def other_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as rsp:
                    json_rsp = await self.get_json_rsp(rsp, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def other_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.post(url, headers=headers, data=data, params=params) as rsp:
                    json_rsp = await self.get_json_rsp(rsp, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def bili_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_session.get(url, headers=headers, data=data, params=params) as rsp:
                    json_rsp = await self.get_json_rsp(rsp, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def session_text_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as rsp:
                    text_rsp = await self.get_text_rsp(rsp, url)
                    if text_rsp is not None:
                        return text_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    @staticmethod
    async def request_playurl(cid):
        inst = bilibili.instance
        # cid real_roomid
        # url = 'http://api.live.bilibili.com/room/v1/Room/playUrl?'
        url = f'{base_url}/api/playurl?device=phone&platform=ios&scale=3&build=10000&cid={cid}&otype=json&platform=h5'
        json_rsp = await inst.bili_session_get(url)
        return json_rsp

    @staticmethod
    async def request_search_liveuser(name):
        inst = bilibili.instance
        search_url = f'https://search.bilibili.com/api/search?search_type=live_user&keyword={name}&page=1'
        json_rsp = await inst.other_session_get(search_url)
        return json_rsp

    @staticmethod
    async def request_search_biliuser(name):
        inst = bilibili.instance
        search_url = f"https://search.bilibili.com/api/search?search_type=bili_user&keyword={name}"
        json_rsp = await inst.other_session_get(search_url)
        return json_rsp

    @staticmethod
    async def request_fetch_capsule():
        inst = bilibili.instance
        url = f"{base_url}/api/ajaxCapsule"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def request_open_capsule(count):
        inst = bilibili.instance
        url = f"{base_url}/api/ajaxCapsuleOpen"
        data = {
            'type': 'normal',
            "count": count,
            "csrf_token": inst.dic_bilibili['csrf']
        }
        json_rsp = await inst.bili_session_post(url, data=data, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    def request_logout():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&access_token={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/revoke'
        data = f'{params}&sign={sign}'
        appheaders = {**(inst.dic_bilibili['appheaders']), 'cookie': ''}
        rsp = inst.login_session_post(true_url, params=data, headers=appheaders)
        print(rsp.json())
        return rsp

    # 1:900兑换
    @staticmethod
    async def request_doublegain_coin2silver():
        inst = bilibili.instance
        # url: "/exchange/coin2silver",
        data = {'coin': 10}
        url = f"{base_url}/exchange/coin2silver"
        json_rsp = await inst.bili_session_post(url, data=data, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def post_watching_history(room_id):
        inst = bilibili.instance
        data = {
            "room_id": room_id,
            "csrf_token": inst.dic_bilibili['csrf']
        }
        url = f"{base_url}/room/v1/Room/room_entry_action"
        json_rsp = await inst.bili_session_post(url, data=data, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def silver2coin_web():
        inst = bilibili.instance
        url = f"{base_url}/pay/v1/Exchange/silver2coin"
        data = {
            "platform": 'pc',
            "csrf_token": inst.dic_bilibili['csrf']
        }
        json_rsp = await inst.bili_session_post(url, headers=inst.dic_bilibili['pcheaders'], data=data)
        return json_rsp

    @staticmethod
    async def silver2coin_app():
        inst = bilibili.instance
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={CurrentTime()}'
        sign = inst.calc_sign(temp_params)
        app_url = f"{base_url}/AppExchange/silver2coin?{temp_params}&sign={sign}"
        json_rsp = await inst.bili_session_post(app_url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def request_fetch_fan(real_roomid, uid):
        inst = bilibili.instance
        url = f'{base_url}/rankdb/v1/RoomRank/webMedalRank?roomid={real_roomid}&ruid={uid}'
        json_rsp = await inst.bili_session_get(url)
        return json_rsp

    @staticmethod
    async def request_check_room(roomid):
        inst = bilibili.instance
        url = f"{base_url}/room/v1/Room/room_init?id={roomid}"
        json_rsp = await inst.bili_session_get(url)
        return json_rsp

    @staticmethod
    async def request_fetch_bag_list():
        inst = bilibili.instance
        url = f"{base_url}/gift/v2/gift/bag_list"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def request_check_taskinfo():
        inst = bilibili.instance
        url = f'{base_url}/i/api/taskInfo'
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def request_send_gift_web(giftid, giftnum, bagid, ruid, biz_id):
        inst = bilibili.instance
        url = f"{base_url}/gift/v2/live/bag_send"
        data = {
            'uid': inst.dic_bilibili['uid'],
            'gift_id': giftid,
            'ruid': ruid,
            'gift_num': giftnum,
            'bag_id': bagid,
            'platform': 'pc',
            'biz_code': 'live',
            'biz_id': biz_id,
            'rnd': CurrentTime(),
            'storm_beat_id': '0',
            'metadata': '',
            'price': '0',
            'csrf_token': inst.dic_bilibili['csrf']
        }
        json_rsp = await inst.bili_session_post(url, headers=inst.dic_bilibili['pcheaders'], data=data)
        return json_rsp

    @staticmethod
    async def request_fetch_user_info():
        inst = bilibili.instance
        url = f"{base_url}/i/api/liveinfo"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def request_fetch_user_infor_ios():
        inst = bilibili.instance
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&platform=ios'
        url = f'{base_url}/mobile/getUser?{temp_params}'
        json_rsp = await inst.bili_session_get(url)
        return json_rsp

    @staticmethod
    async def request_fetch_liveuser_info(real_roomid):
        inst = bilibili.instance
        url = f'{base_url}/live_user/v1/UserInfo/get_anchor_in_room?roomid={real_roomid}'
        json_rsp = await inst.bili_session_get(url)
        return json_rsp

    @staticmethod
    async def request_load_img(url):
        return await bilibili.instance.other_session.get(url)

    @staticmethod
    async def request_send_danmu_msg_web(msg, roomId):
        inst = bilibili.instance
        url = f'{base_url}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(roomId),
            'csrf_token': inst.dic_bilibili['csrf'],
            'csrf': inst.dic_bilibili['csrf']
        }

        json_rsp = await inst.bili_session_post(url, headers=inst.dic_bilibili['pcheaders'], data=data)
        return json_rsp

    @staticmethod
    async def request_fetchmedal():
        inst = bilibili.instance
        url = f'{base_url}/i/api/medal?page=1&pageSize=50'
        json_rsp = await inst.bili_session_post(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def ReqWearingMedal():
        inst = bilibili.instance
        url = f'{base_url}/live_user/v1/UserInfo/get_weared_medal'
        data = {
            'uid': inst.dic_bilibili['uid'],
            'csrf_token': ''
        }
        json_rsp = await inst.bili_session_post(url, data=data, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def ReqTitleInfo():
        inst = bilibili.instance
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}'
        sign = inst.calc_sign(temp_params)
        url = f'{base_url}/appUser/myTitleList?{temp_params}&sign={sign}'
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    def request_getkey():
        inst = bilibili.instance
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={inst.dic_bilibili["appkey"]}'
        sign = inst.calc_sign(temp_params)
        params = {'appkey': inst.dic_bilibili['appkey'], 'sign': sign}
        response = inst.login_session_post(url, data=params)
        return response

    @staticmethod
    def normal_login(username, password, captcha=None):
        inst = bilibili.instance
        if captcha is None:
            captcha = ''
        temp_params = f'actionKey={inst.dic_bilibili["actionKey"]}&appkey={inst.dic_bilibili["appkey"]}&build={inst.dic_bilibili["build"]}&captcha={captcha}&device={inst.dic_bilibili["device"]}&mobi_app={inst.dic_bilibili["mobi_app"]}&password={password}&platform={inst.dic_bilibili["platform"]}&username={username}'
        sign = inst.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        response = inst.login_session_post(url, params=payload)
        return response

    @staticmethod
    def get_captcha(username, password):
        inst = bilibili.instance
        
        # with requests.Session() as s:
        url = "https://passport.bilibili.com/captcha"
        res = inst.login_session_get(url)
        # print(res.content)
        # print(res.content)

        captcha = cnn_captcha(res.content)
        return captcha
        
    @staticmethod
    def request_check_token():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        response1 = inst.login_session_get(true_url, headers=inst.dic_bilibili['appheaders'])
        return response1

    @staticmethod
    def request_refresh_token():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&access_token={inst.dic_bilibili["access_key"]}&{inst.app_params}&refresh_token={inst.dic_bilibili["refresh_token"]}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        response1 = inst.login_session_post(url, headers=inst.dic_bilibili['appheaders'], params=payload)
        return response1

    @staticmethod
    async def get_giftlist_of_storm(roomid):
        inst = bilibili.instance
        get_url = f"{base_url}/lottery/v1/Storm/check?roomid={roomid}"
        json_rsp = await inst.bili_session_get(get_url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_gift_of_storm(id):
        inst = bilibili.instance
        storm_url = f'{base_url}/lottery/v1/Storm/join'
        payload = {
            "id": id,
            "color": "16777215",
            "captcha_token": "",
            "captcha_phrase": "",
            "token": "",
            "csrf_token": inst.dic_bilibili['csrf']}
        json_rsp = await inst.bili_session_post(storm_url, data=payload, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_gift_of_events_web(text1, text2, raffleid):
        inst = bilibili.instance
        headers = {
            **(inst.dic_bilibili['pcheaders']),
            'referer': text2
            }
        
        pc_url = f'{base_url}/activity/v1/Raffle/join?roomid={text1}&raffleId={raffleid}'
        json_rsp = await inst.bili_session_get(pc_url, headers=headers)

        return json_rsp

    @staticmethod
    async def get_gift_of_events_app(text1, raffleid):
        inst = bilibili.instance
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&actionKey={inst.dic_bilibili["actionKey"]}&appkey={inst.dic_bilibili["appkey"]}&build={inst.dic_bilibili["build"]}&device={inst.dic_bilibili["device"]}&event_type={raffleid}&mobi_app={inst.dic_bilibili["mobi_app"]}&platform={inst.dic_bilibili["platform"]}&room_id={text1}&ts={CurrentTime()}'
        # params = temp_params + inst.dic_bilibili['app_secret']
        sign = inst.calc_sign(temp_params)
        true_url = f'{base_url}/YunYing/roomEvent?{temp_params}&sign={sign}'
        json_rsp = await inst.bili_session_get(true_url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp
   
    @staticmethod
    async def get_gift_of_TV(real_roomid, TV_raffleid):
        inst = bilibili.instance
        url = f"{base_url}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": TV_raffleid,
            "type": "Gift",
            "csrf_token": ''
            }
            
        json_rsp = await inst.bili_session_post(url, data=payload, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def get_gift_of_TV_app(real_roomid, raffle_id, raffle_type):
        inst = bilibili.instance
        url = f"{base_url}/gift/v4/smalltv/getAward"
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&raffleId={raffle_id}&roomid={real_roomid}&ts={CurrentTime()}&type={raffle_type}'
        sign = inst.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        # print(payload)
        json_rsp = await inst.bili_session_post(url, params=payload, headers=inst.dic_bilibili['appheaders'])
        # print(json_rsp)
        return json_rsp
        
    @staticmethod
    async def get_gift_of_guard(roomid, id):
        inst = bilibili.instance
        join_url = f"{base_url}/lottery/v2/Lottery/join"
        data = {
            'roomid': roomid,
            'id': id,
            'type': 'guard',
            'csrf_token': inst.dic_bilibili['csrf']
        }
        json_rsp = await inst.bili_session_post(join_url, data=data, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_giftlist_of_events(text1):
        inst = bilibili.instance
        # url = f'{base_url}/activity/v1/Raffle/check?roomid={text1}'
        temp_params = f'{base_url}/activity/v1/Common/mobileRoomInfo?access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&roomid={text1}&ts={CurrentTime()}'
        sign = inst.calc_sign(temp_params)
        url = f'{base_url}/activity/v1/Common/mobileRoomInfo?{temp_params}&sign={sign}'
        json_rsp = await bilibili.instance.bili_session_get(url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def get_giftlist_of_TV(real_roomid):
        inst = bilibili.instance
        url = f"{base_url}/gift/v3/smalltv/check?roomid={real_roomid}"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def get_giftlist_of_guard(roomid):
        inst = bilibili.instance
        true_url = f'{base_url}/lottery/v1/Lottery/check_guard?roomid={roomid}'
        json_rsp = await inst.bili_session_get(true_url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_activity_result(activity_roomid, activity_raffleid):
        inst = bilibili.instance
        url = f"{base_url}/activity/v1/Raffle/notice?roomid={activity_roomid}&raffleId={activity_raffleid}"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_TV_result(TV_roomid, TV_raffleid):
        inst = bilibili.instance
        url = f"{base_url}/gift/v3/smalltv/notice?type=small_tv&raffleId={TV_raffleid}"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def pcpost_heartbeat():
        inst = bilibili.instance
        url = f'{base_url}/User/userOnlineHeart'
        json_rsp = await inst.bili_session_post(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    # 发送app心跳包
    @staticmethod
    async def apppost_heartbeat():
        inst = bilibili.instance
        time = CurrentTime()
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={time}'
        sign = inst.calc_sign(temp_params)
        url = f'{base_url}/mobile/userOnlineHeart?{temp_params}&sign={sign}'
        payload = {'roomid': 23058, 'scale': 'xhdpi'}
        json_rsp = await inst.bili_session_post(url, data=payload, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    # 心跳礼物
    @staticmethod
    async def heart_gift():
        inst = bilibili.instance
        url = f"{base_url}/gift/v2/live/heart_gift_receive?roomid=3&area_v2_id=34"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_lotterylist(i):
        inst = bilibili.instance
        url = f"{base_url}/lottery/v1/box/getStatus?aid={i}"
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_gift_of_lottery(i, g):
        inst = bilibili.instance
        url1 = f'{base_url}/lottery/v1/box/draw?aid={i}&number={g + 1}'
        json_rsp = await inst.bili_session_get(url1, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_time_about_silver():
        inst = bilibili.instance
        time = CurrentTime()
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={time}'
        sign = inst.calc_sign(temp_params)
        GetTask_url = f'{base_url}/mobile/freeSilverCurrentTask?{temp_params}&sign={sign}'
        json_rsp = await inst.bili_session_get(GetTask_url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def get_silver(timestart, timeend):
        inst = bilibili.instance
        time = CurrentTime()
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&time_end={timeend}&time_start={timestart}&ts={time}'
        sign = inst.calc_sign(temp_params)
        url = f'{base_url}/mobile/freeSilverAward?{temp_params}&sign={sign}'
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def get_dailybag():
        inst = bilibili.instance
        url = f'{base_url}/gift/v2/live/receive_daily_bag'
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_dosign():
        inst = bilibili.instance
        url = f'{base_url}/sign/doSign'
        json_rsp = await inst.bili_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def get_dailytask():
        inst = bilibili.instance
        url = f'{base_url}/activity/v1/task/receive_award'
        payload2 = {'task_id': 'double_watch_task'}
        json_rsp = await inst.bili_session_post(url, data=payload2, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def get_grouplist():
        inst = bilibili.instance
        url = "https://api.vc.bilibili.com/link_group/v1/member/my_groups"
        json_rsp = await inst.other_session_get(url, headers=inst.dic_bilibili['pcheaders'])
        return json_rsp

    @staticmethod
    async def assign_group(i1, i2):
        inst = bilibili.instance
        temp_params = f'access_key={inst.dic_bilibili["access_key"]}&actionKey={inst.dic_bilibili["actionKey"]}&appkey={inst.dic_bilibili["appkey"]}&build={inst.dic_bilibili["build"]}&device={inst.dic_bilibili["device"]}&group_id={i1}&mobi_app={inst.dic_bilibili["mobi_app"]}&owner_id={i2}&platform={inst.dic_bilibili["platform"]}&ts={CurrentTime()}'
        sign = inst.calc_sign(temp_params)
        url = f'https://api.vc.bilibili.com/link_setting/v1/link_setting/sign_in?{temp_params}&sign={sign}'
        json_rsp = await inst.other_session_get(url, headers=inst.dic_bilibili['appheaders'])
        return json_rsp

    @staticmethod
    async def gift_list():
        url = f"{base_url}/gift/v3/live/gift_config"
        res = await bilibili.instance.bili_session_get(url)
        return res
        
    @staticmethod
    async def req_realroomid(areaid):
        url = f'{base_url}/room/v1/area/getRoomList?platform=web&parent_area_id={areaid}&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30'
        json_rsp = await bilibili.instance.bili_session_get(url)
        return json_rsp
     
    @staticmethod
    async def req_room_init(roomid):
        url = f'{base_url}/room/v1/Room/room_init?id={roomid}'
        json_rsp = await bilibili.instance.bili_session_get(url)
        return json_rsp
    
    @staticmethod
    async def ReqRoomInfo(roomid):
        inst = bilibili.instance
        url = f"{base_url}/room/v1/Room/get_info?room_id={roomid}"
        res = await inst.bili_session_get(url)
        return res

    async def ReqGiveCoin2Av(self, video_id, num):
        url = 'https://api.bilibili.com/x/web-interface/coin/add'
        pcheaders = {
            **(self.dic_bilibili['pcheaders']),
            'referer': f'https://www.bilibili.com/video/av{video_id}'
            }
        data = {
            'aid': video_id,
            'multiply': num,
            'cross_domain': 'true',
            'csrf': self.dic_bilibili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=pcheaders, data=data)
        return json_rsp

    async def Heartbeat(self, aid, cid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        data = {'aid': aid, 'cid': cid, 'mid': self.dic_bilibili['uid'], 'csrf': self.dic_bilibili['csrf'],
                'played_time': 0, 'realtime': 0,
                'start_ts': int(time.time()), 'type': 3, 'dt': 2, 'play_type': 1}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dic_bilibili['pcheaders'])
        return json_rsp

    async def ReqMasterInfo(self):
        url = 'https://account.bilibili.com/home/reward'
        json_rsp = await self.other_session_get(url, headers=self.dic_bilibili['pcheaders'])
        return json_rsp

    async def ReqVideoCid(self, video_aid):
        url = f'https://www.bilibili.com/widget/getPageList?aid={video_aid}'
        json_rsp = await self.other_session_get(url)
        return json_rsp

    async def DailyVideoShare(self, video_aid):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {'aid': video_aid, 'jsonp': 'jsonp', 'csrf': self.dic_bilibili['csrf']}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dic_bilibili['pcheaders'])
        return json_rsp
    
    async def req_fetch_uper_video(self, mid, page):
        url = f'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={mid}&pagesize=100&page={page}'
        json_rsp = await self.other_session_get(url)
        return json_rsp
                
    async def req_fetch_av(self):
        text_tsp = await self.session_text_get('https://www.bilibili.com/ranking/all/0/0/1/')
        return text_tsp
    
    async def req_vote_case(self, id, vote):
        url = 'http://api.bilibili.com/x/credit/jury/vote'
        payload = {
            "jsonp": "jsonp",
            "cid": id,
            "vote": vote,
            "content": "",
            "likes": "",
            "hates": "",
            "attr": "1",
            "csrf": ConfigLoader().dic_bilibili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=self.dic_bilibili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_fetch_case(self):
        url = 'http://api.bilibili.com/x/credit/jury/caseObtain'
        payload = {
            "jsonp": "jsonp",
            "csrf": ConfigLoader().dic_bilibili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=self.dic_bilibili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_check_voted(self, id):
        headers = {
            **(self.dic_bilibili['pcheaders']),
            "Referer": f'https://www.bilibili.com/judgement/vote/{id}',
            }
        
        url = f'https://api.bilibili.com/x/credit/jury/juryCase?jsonp=jsonp&callback=jQuery1720{randomint()}_{CurrentTime()}&cid={id}&_={CurrentTime()}'
        text_rsp = await self.session_text_get(url, headers=headers)
        # print(text_rsp)
        return text_rsp
