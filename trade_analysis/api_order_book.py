from requests import get
from requests.compat import urljoin
from json import dumps
from accounts import coinmarketcap_api_key

url_base = 'https://pro-api.coinmarketcap.com'
endpoint = '/v1/exchange/listings/historical'
response = get(urljoin(url_base, endpoint), headers={'X-CMC_PRO_API_KEY':coinmarketcap_api_key})
print(response.status_code)
print(dumps(response.text))