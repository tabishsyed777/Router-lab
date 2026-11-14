"""Fresh-server HTTP outcome checks; no candidate code runs on the host."""
import http.client
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit
from uuid import uuid4


def matches_echo(status,body,path,query,method,payload,request_id):
    return status==200 and isinstance(body,dict) and all(body.get(key)==value for key,value in {
        'path':path,'query':query,'method':method,'body':payload,
        'forwarded_for':'127.0.0.1','request_id':request_id}.items())


def request(path,method='GET',body='',headers=None):
    connection=http.client.HTTPConnection('127.0.0.1',8080,timeout=3)
    try:
        connection.request(method,path,body.encode(),headers or {})
        response=connection.getresponse()
        content=response.read(131072).decode()
        try:
            parsed=json.loads(content)
        except ValueError:
            parsed=content
        return response.status,dict(response.getheaders()),parsed
    finally:
        connection.close()


def evaluate():
    checks=[]
    def check(name,passed,detail=''):
        checks.append({'name':name,'passed':bool(passed),'detail':str(detail)[:2000]})
    backend=subprocess.Popen(['python3','/app/backend.py'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    proxy=None
    try:
        syntax=subprocess.run(['/usr/sbin/runuser','-u','proxyuser','--','nginx','-t','-c','/app/nginx.conf','-p','/tmp/'],capture_output=True,text=True,timeout=5)
        check('nginx_configuration',syntax.returncode==0,syntax.stderr)
        if syntax.returncode:
            return {'passed':False,'checks':checks}
        proxy=subprocess.Popen(['/usr/sbin/runuser','-u','proxyuser','--','nginx','-c','/app/nginx.conf','-p','/tmp/','-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+8
        ready=False
        while time.monotonic()<deadline:
            try:
                request('/health')
                # Wait for both sockets, without assuming the proxy health behavior is correct.
                connection=http.client.HTTPConnection('127.0.0.1',9001,timeout=.5)
                connection.request('GET','/ready'); response=connection.getresponse(); response.read(); connection.close()
                ready=True
                break
            except (OSError,http.client.HTTPException):
                time.sleep(.05)
        check('fresh_servers_ready',ready)
        if not ready:
            return {'passed':False,'checks':checks}
        status,headers,body=request('/health')
        check('public_health',status==200 and body=={'status':'ok'})
        for index,headers in enumerate([{}, {'Authorization':'Bearer wrong'}, {'X-Authorization':'Bearer route-lab-token'}, {'Authorization':'Basic route-lab-token'}]):
            status,_,_=request('/api/items/7',headers=headers)
            check(f'authorization_rejection_{index}',status==401)
        for path in ['/','/private','/apiary/items']:
            status,_,_=request(path)
            check('unknown_path_'+path,status==404)
        status,headers,_=request('/api?keep=yes')
        location=urlsplit(headers.get('Location',''))
        check('exact_prefix_redirect',status==308 and location.path=='/api/' and location.query=='keep=yes' and (not location.netloc or location.netloc=='127.0.0.1:8080'))
        for index,method in enumerate(['GET','POST','GET','POST']):
            nonce=uuid4().hex[:12]
            path=f'/items/{700+index}/{nonce}'
            query=f'filter={nonce}&page={index+1}'
            payload=f'body-{nonce}' if method=='POST' else ''
            request_id=f'req-{nonce}'
            auth={'Authorization':'Bearer route-lab-token','X-Forwarded-For':'198.51.100.77','X-Request-ID':request_id,'Content-Type':'text/plain'}
            status,_,body=request('/api'+path+'?'+query,method,payload,auth)
            check(f'forwarded_request_{index}',matches_echo(status,body,path,query,method,payload,request_id),body)
    finally:
        for process in [proxy,backend]:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=3)
    return {'passed':all(item['passed'] for item in checks),'checks':checks}


def main():
    try:
        report=evaluate()
    except Exception as error:
        report={'passed':False,'checks':[{'name':'verifier_execution','passed':False,'detail':str(error)}]}
    directory=Path('/logs/verifier');directory.mkdir(parents=True,exist_ok=True);directory.chmod(0o700)
    (directory/'details.json').write_text(json.dumps(report,indent=2)+'\n')
    (directory/'reward.txt').write_text('1\n' if report['passed'] else '0\n')
    print(json.dumps(report))


if __name__=='__main__':
    main()
