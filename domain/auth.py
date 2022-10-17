

class GoogleClientScope:
    Drive = ['https://www.googleapis.com/auth/drive']
    Gmail = ['https://www.googleapis.com/auth/gmail.readonly']


class ClientScope:
    EMAIL_GATEWAY_API = 'api://4ff83655-c28e-478f-b384-08ca8e98a811/.default'
    TwilioGatewayApi = 'api://608043f8-87a6-46bd-ab49-1b73de73a6ec/.default'
    AzureGatewayApi = 'api://a6d4c26f-f77c-41dc-b732-eb82ac0fbe39/.default'
    VAULT_API = 'api://0a91113d-07e5-4820-a226-62e14e08b835/.default'


class AuthScheme:
    Read = 'read'
    Write = 'write'
    Sync = 'sync'


class AdRole:
    Read = 'Fitness.Read'
    Write = 'Fitness.Write'
    Sync = 'Fitness.Sync'
