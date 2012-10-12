#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import hmac
import hashlib
import time
import logging
import json

import requests

App_Key="2000904490"
App_Secret="0e4514df35df979dd1e58681319246e7"

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.DEBUG,datefmt='%m/%d %H:%M:%S')

## a wrapper function to request particular data to particular url
## logging the json info
## and return the reponse.json
def Vrequest(method,**kwargs):
    if method not in ['GET','POST']:
        logging.error("wrong method: %s"%method)
        return
    ## sometimes the api return nothing.
    while True:
        response=requests.request(method.lower(),**kwargs)
        if response.json is not None:
            returnedJson=response.json
            assert returnedJson.get("err_code") in [0,602],"fail.error code: %s,error message: %s" \
                   %(returnedJson["err_code"],returnedJson["err_msg"].encode('utf-8'))
            logging.info('success.')
            return returnedJson

class VdiskUser():
    
    def __init__(self,account,password,app_type=None):
        self.account=account
        self.password=password
        self.token=None
        self.app_type=app_type
        self.dologid=None
        self.used=None
        self.total=None

    def is_loged(self):
        return self.token is not None

    def get_token(self):
        url="http://openapi.vdisk.me/?m=auth&a=get_token"
        t=int(time.time())
        if self.app_type is None:
            self.app_type="local"
        signature=hmac.new(App_Secret,"account="+self.account
                           +"&appkey="+App_Key+"&password="+
                           self.password+"&time="+
                           repr(t),hashlib.sha256).hexdigest()
        data=dict(account=self.account,
                  password=self.password,
                  appkey=App_Key,time=t,
                  signature=signature,
                  app_type=self.app_type)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        self.token=returnedJson["data"]["token"]
        return returnedJson

    ## keep alive
    def keep(self):
        url="http://openapi.vdisk.me/?a=keep"
        data=dict(token=self.token,dilogid=self.dologid) if self.dologid!=None \
              else dict(token=self.token)
        time.sleep(0.5)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        if returnedJson['err_code'] in [0,602]:
            self.dologid=returnedJson['dologid']
            
    def get_quota(self):
        url="http://openapi.vdisk.me/?m=file&a=get_quota"
        data=dict(token=self.token)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        self.used=returnedJson['data']['used']
        self.total=returnedJson['data']['total']
        logging.warning('used: %s'%returnedJson['data']['used'])
        logging.warning('total: %s'%returnedJson['data']['total'])
        return returnedJson

    ## a token will expire after 15 minutes,
    ## so keep_token() should run about 10 to 15 minutes
    def keep_token(self):
        url="http://openapi.vdisk.me/?m=user&a=keep_token"
        self.keep()
        data=dict(token=self.token,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        self.check_dologid(returnedJson)
        return returnedJson

# handle file and dir etc.
class VdiskFile(VdiskUser):
    
    ## upload and share,a file size must less than 10M
    ## there is another upload_file in vdisk api.but it donot share
    def upload_file(self,afile,dir_id=0,cover=None):
        url="http://openapi.vdisk.me/?m=file&a=upload_share_file"
        if cover is None:
            cover="yes"
        files={'file':open(afile,'r')}
        self.keep()
        data=dict(token=self.token,dir_id=dir_id,
                  cover=cover,dologid=self.dologid)
        returnedJson=Vrequest('POST',**dict(url=url,data=data,files=files))
        return returnedJson

    def delete_file(self,fid):
        url="http://openapi.vdisk.me/?m=file&a=delete_file"
        self.keep()
        data=dict(token=self.token,fid=fid,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson

    def recycle_del_file(self,fid):
        url='http://openapi.vdisk.me/?m=recycle&a=delete_file'
        self.keep()
        data=dict(token=self.token,fid=fid,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
    
    def get_dir_list(self,dir_id=0):
        url="http://openapi.vdisk.me/?m=dir&a=getlist"
        data=dict(token=self.token,dir_id=dir_id)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
                    
    def get_file_info(self,fid):
        url="http://openapi.vdisk.me/?m=file&a=get_file_info"
        self.keep()
        data=dict(token=self.token,fid=fid,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
    
    def upload_with_sha1(self,sha1,file_name,dir_id=0):
        url="http://openapi.vdisk.me/?m=file&a=upload_with_sha1"
        self.keep()
        data=dict(token=self.token,dir_id=dir_id,sha1=sha1,
                  file_name=file_name,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
        
    def share_file(self,fid):
        url="http://openapi.vdisk.me/?m=file&a=share_file"
        self.keep()
        data=dict(token=self.token,fid=fid,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
    
    def create_dir(self,create_name,parent_id=0):
        url="http://openapi.vdisk.me/?m=dir&a=create_dir"
        self.keep()
        data=dict(token=self.token,create_name=create_name,
                  parent_id=parent_id,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson
    
    def delete_dir(self,dir_id):
        url="http://openapi.vdisk.me/?m=dir&a=delete_dir"
        self.keep()
        data=dict(token=self.token,dir_id=dir_id,dologid=self.dologid)
        returnedJson=Vrequest("POST",**dict(url=url,data=data))
        return returnedJson

def main():
    parser=argparse.ArgumentParser(description="Sina Vdisk")
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--upload","-U",help="Upload a file")
    group.add_argument("--delete","-D",help="Delete a file")
    group.add_argument("--query","-Q",help="Query file by key word")

    args=parser.parse_args()

    if args.upload:
        print args.upload
    elif args.delete:
        print args.delete
    elif args.query:
        print args.query
    else:
        pass

if __name__='__main__':
    main()
