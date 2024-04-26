import base64
import urllib.parse
import urllib.request
from os import environ

if __name__ == "__main__":
    data = urllib.parse.urlencode({"TESTPLAN": "full"}).encode()
    url = "http://10.102.156.15:8080/job/cert-stock-sru-focal-server-adlink-ampere-altra-developer-platform-c30097//buildWithParameters"
    opener = urllib.request.build_opener()
    credentials = f"admin:{environ['JENKINS_API_TOKEN']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    opener.addheaders = [("Authorization", f"Basic {encoded_credentials}")]
    opener.open(url, data)
