import json
import requests
import datetime
import hashlib
import hmac
import base64
import uuid

class databrickslog:

    def __init__(self, workspaceid, workspacekey,logtable, notebook):
        self.wks_id = workspaceid
        self.wks_shared_key = workspacekey
        self.log_type = logtable
        self.nbook = notebook

    #Build the API signature
    def __build_signature(self,customer_id, shared_key, date, content_length, method, content_type, resource):
        x_headers = 'x-ms-date:' + date
        string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
        bytes_to_hash = str.encode(string_to_hash,'utf-8')  
        decoded_key = base64.b64decode(shared_key)
        encoded_hash = (base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest())).decode()
        authorization = "SharedKey {}:{}".format(customer_id,encoded_hash)
        return authorization

    #Build and send a request to the POST API
    def __post_data(self,  body):
        method = 'POST'
        content_type = 'application/json'
        resource = '/api/logs'
        rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        content_length = len(body)
        signature = self.__build_signature(self.wks_id, self.wks_shared_key, rfc1123date, content_length, method, content_type, resource)
        uri = 'https://' + self.wks_id + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'

        headers = {
            'content-type': content_type,
            'Authorization': signature,
            'Log-Type': self.log_type,
            'x-ms-date': rfc1123date
        }

        response = requests.post(uri,data=body, headers=headers)
        if (response.status_code >= 200 and response.status_code <= 299):
            print ('Accepted')
        else:
            print ("Response code: {}".format(response.status_code))



    def start_notebook(self):
        timenow= datetime.datetime.utcnow()
        self.stepid = 1
        self.starttime = timenow
        self.previoustime = timenow
        self.guid = str(uuid.uuid4())
        json_data = [{
            "time_generated": timenow.strftime('%a, %d %b %Y %H:%M:%S GMT') ,
            "guid" : self.guid,
            "notebook": self.nbook,
            "step_id" : self.stepid,
            "action" : "starting notebook",
            "duration_from_laststep" :  str(timenow - self.previoustime),
            "total_duration": ""            
            }]
        body = json.dumps(json_data)
        self.__post_data(body)
        
        
    def stop_notebook(self):
        timenow= datetime.datetime.utcnow()
        self.stepid+=1
        json_data = [{
            "time_generated": timenow.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "guid" : self.guid,
            "notebook": self.nbook,
            "step_id" : self.stepid,
            "action" : "end notebook",
            "duration_from_laststep" : str(timenow - self.previoustime),
            "total_duration": str(timenow - self.starttime)
            }]
        body = json.dumps(json_data)
        self.__post_data(body)


    def step_notebook(self, customlog = None):
        timenow= datetime.datetime.utcnow()
        self.stepid+=1
        json_data = [{
            "time_generated": timenow.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "guid" : self.guid,
            "notebook": self.nbook,
            "step_id" : self.stepid,
            "action" : "step notebook",
            "duration_from_laststep" : str(timenow - self.previoustime)
            }]
        if(customlog):
            json_data[0]["customlog"] = customlog
        
        body = json.dumps(json_data)
        self.previoustime = timenow
        self.__post_data(body)

