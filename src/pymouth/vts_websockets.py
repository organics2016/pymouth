import json
import os

from websockets.sync.client import connect, ClientConnection


class VTSParameterData:
    def __init__(self, id: str, value: any):
        self.id = id
        self.value = value


class VTSPluginInfo:
    def __init__(self, plugin_name: str, developer: str, authentication_token_path: str, plugin_icon: str = None):
        self.plugin_name = plugin_name
        self.developer = developer
        self.authentication_token_path = authentication_token_path
        self.plugin_icon = plugin_icon


class VTSWebSocket:
    def __init__(self, ws_uri: str, plugin_info: VTSPluginInfo):
        self.ws_uri = ws_uri
        self.plugin_info = plugin_info
        self.req_msg = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
        }

        self.client: ClientConnection | None = None
        self.vts_token = None

    def close(self):
        assert self.client is not None
        self.client.close()

    def request(self, api: str, req_id: str = None, data: dict = None, response: bool = True) -> any:
        assert self.client is not None
        req = {**self.req_msg, "requestID": api if req_id is None else req_id, "messageType": api}
        if data is not None:
            req = {**req, "data": data}
        self.client.send(json.dumps(req, ensure_ascii=False, skipkeys=True))
        res = self.client.recv()
        if response:
            return json.loads(res)

    def connect(self):
        self.client = connect(uri=self.ws_uri)
        res = self.request('APIStateRequest')
        if res['data']['currentSessionAuthenticated'] is True:
            return
        if os.path.exists(self.plugin_info.authentication_token_path):
            with open(self.plugin_info.authentication_token_path, 'r', encoding='utf-8') as f:
                self.vts_token = f.read()
        else:
            self.authenticate_token()

        if self.authenticate():
            return

        self.authenticate_token()
        if self.authenticate() is False:
            raise Exception('Authentication failed')

    def authenticate(self) -> bool:
        assert self.vts_token is not None
        res = self.request('AuthenticationRequest', data={"pluginName": self.plugin_info.plugin_name,
                                                          "pluginDeveloper": self.plugin_info.developer,
                                                          "authenticationToken": self.vts_token})
        return res['data']['authenticated']

    def authenticate_token(self):
        res = self.request('AuthenticationTokenRequest', data={"pluginName": self.plugin_info.plugin_name,
                                                               "pluginDeveloper": self.plugin_info.developer,
                                                               "pluginIcon": self.plugin_info.plugin_icon})
        self.vts_token = res['data']['authenticationToken']
        with open(self.plugin_info.authentication_token_path, 'w', encoding='utf-8') as f:
            f.write(self.vts_token)

    def set_params(self, params: list[VTSParameterData]):
        data = {
            "faceFound": False,
            "mode": "add",
            "parameterValues": [d.__dict__ for d in params],
        }
        self.request('InjectParameterDataRequest', data=data, response=False)

    def set_single_param(self, param: VTSParameterData):
        self.set_params([param])

# ws = VTSWebSocket()
# ws.connect()
# ss = VTSParameterData('MouthOpen', 0.9)
# ws.set_single_param(ss)
# print(json.dumps(ss.__dict__))
