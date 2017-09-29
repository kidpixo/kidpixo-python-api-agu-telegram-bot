# api.developer.agu
# mario.damore@dlr.de
# dikxip_DVLPRG

import requests
import json
import attr
# [Making a request to a RESTful API using python - Stack Overflow]
# (https://stackoverflow.com/questions/17301938/making-a-request-to-a-restful-api-using-python)
baseurl = 'https://api.developer.agu.org:8443/'


def api_channel_url(ch):
    return '{}api/{}'.format(baseurl, ch)


def urlencoder(paradict):
    from urllib.parse import urlencode
    out = urlencode({k: v for k, v in paradict.items() if k is not 'params'})
    if 'params' in paradict.keys():
        out = '%s&params=%s' % (out, urlencode(paradict['params']))
    return out


def ceildiv(a, b):
    return -(-a // b)


@attr.s
class Token(object):
    baseurl = attr.ib(default=None)
    token = attr.ib(default=None)
    lastUpdate = attr.ib(default=None)

    def _get_auth(self):
        '''Ask for a token. If not ok, separate the bad credentials from other cases '''
        headers_auth = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        payload_auth = {"username": "YOURUSERNAME", # CHANGE HERE!!
                        "password": "YOURPASSWORD"} # CHANGE HERE!!
        auth_req = requests.post(self.baseurl+'security/auth', headers=headers_auth, json=payload_auth)
        if(auth_req.ok):
            return auth_req.json()['token']
        else:
            print('Status Code : %s \n' % auth_req.status_code, json.dumps(auth_req.json(), indent=4))
            if "org.springframework.security.authentication.BadCredentialsException" in auth_req.json().values():
                raise UserWarning('bad credentials asking for the token')
            else:
                # some other error,raise exception for the specific status
                auth_req.raise_for_status()

    def __attrs_post_init__(self):
        """Assign Token.token after __init__"""
        import pytz
        import datetime
        self.token = self._get_auth()
        self.lastUpdate = datetime.datetime.now(pytz.utc)

    def update_token(self):
        """Ask for a new token and update the Token.token variable"""
        self.token = self._get_auth()


# TODO : the token here inside is refreshed only here inside!! Add a class holding the value and methods?
def get_data(api_channel, tk, parameters=None, debug=None):
    '''wrapper around get_data_core only , try to a new token if the request fails.'''
    if parameters:
        # paramters are valid only for abstracts/search!!
        api_channel = '%s?%s' % (api_channel, urlencoder(parameters))
    try:
        return get_data_core(api_channel, tk.token, debug=debug)
    except requests.HTTPError:
        print('HTTPError')
        tk.update_token()
        return get_data_core(api_channel, tk.token, debug=debug)


def get_data_core(api_channel, token, debug=None):
    headers = {'Accept': 'application/json', 'Authorization': token}
    myResponse = requests.get(api_channel_url(api_channel), headers=headers)
    if(myResponse.ok):
        if not debug:
            return myResponse.json()
        else:
            return myResponse
    else:
        # bad auth
        # if myResponse.json()["exception"] == "org.springframework.security.authentication.BadCredentialsException"
        print('Status Code : %s \n' % myResponse.status_code, json.dumps(myResponse.json(), indent=4))
        myResponse.raise_for_status()


# getting a toke during import
tokenObj = Token(baseurl=baseurl)
