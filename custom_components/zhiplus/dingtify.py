import aiohttp

# Logging
import logging
_LOGGER = logging.getLogger(__name__)


async def async_send(conf, message, data=None):
    token = conf['token']
    secret = conf.get('secret')
    url = "https://oapi.dingtalk.com/robot/send?access_token=" + token
    if secret is not None:
        import time
        import hmac
        import hashlib
        import base64
        import urllib
        timestamp = round(time.time() * 1000)
        hmac_code = hmac.new(secret.encode('utf-8'), '{}\n{}'.format(
            timestamp, secret).encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url += '&timestamp=' + str(timestamp) + '&sign=' + sign

    _LOGGER.debug("URL: %s", url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'msgtype': 'text', 'text': {'content': message}}) as response:
            json = await response.json()
            if json['errcode'] != 0:
                _LOGGER.error("RESPONSE: %s", await response.text())
