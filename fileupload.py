#!/usr/bin/env python
# encoding: utf-8

import os, sys, math, requests, cookielib, urllib2, urllib, re, base64


def support_continue(url):
    # 获取文件大小
    headers = { 'Range': 'bytes=0-4' }
    try:
        r = requests.head(url, headers = headers)
        crange = r.headers['content-range']
        total = int(re.match(ur'^bytes 0-4/(\d+)$', crange).group(1))
        print total
        return True
    except:
        print 'xxx'
        pass
    try:
        total = int(r.headers['content-length'])
        print total
    except:
        total = 0
    return False

def download_file(url):
    # 分块下载
    url = 'http://ww1.sinaimg.cn/large/6d44131cgy1fgjld5vsqvj2001001qv7.jpg'
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename

def DownloadData_test1():
    # 断点续传测试1
    url = 'http://ww1.sinaimg.cn/large/6d44131cgy1fgjld5vsqvj2001001qv7.jpg'
    headers = { 'Range': 'bytes=%d-' % 82 }
    result = requests.get(url, stream=True, headers=headers, timeout=120, verify=False)
    return result

def UploadData3(data):
    # 上传数据
    cookies = open('./cookies.txt', 'r').readlines()[0]
    headers = {
        'Accept': '*/*',
        'Referer': 'http://weibo.com/minipublish',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': cookies
    }
    # 将数据追加到图片数据的结尾
    fim = open('./mini.png', 'rb').read()
    fim = fim + data
    files = { 'pic1': fim }
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php?cb=http%3A%2F%2Fweibo.com%2Faj%2Fstatic%2Fupimgback.html%3F_wv%3D5%26callback%3DSTK_ijax_14972685830696&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog&s=rdxt&ori=1'
    result = requests.post(url, files=files, headers=headers, allow_redirects=False)
    # 解析结果
    pid = ''
    if (result.status_code == 302 or result.status_code == 301):
        location = result.headers['location']
        match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
        if (match != None): pid = match.group(1)
    return pid


def UploadData2(data):
    # 上传数据 GOOD
    cookies = open('./cookies.txt', 'r').readlines()[0]
    headers = {
        'Accept': '*/*',
        'Referer': 'http://weibo.com/minipublish',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': cookies
    }
    # 将数据追加到图片数据的结尾
    fim = open('./mini.png', 'rb').read()
    fim = fim + data
    # 
    b64 = base64.b64encode(fim)
    print len(b64)
    files = { 'b64_data': b64 }

    mfiles = [('b64_data', ('', b64, ''))]
    
    url = 'http://picupload.service.weibo.com//interface/pic_upload.php?ori=1&mime=image%2Fjpeg&data=base64&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog'
    result = requests.post(url, files=mfiles, headers=headers, allow_redirects=False)
    # 解析结果
    print result.text
    '''
    pid = ''
    if (result.status_code == 302 or result.status_code == 301):
        location = result.headers['location']
        match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
        if (match != None): pid = match.group(1)
    return pid
    '''

def UploadData1(data):
    # 上传数据
    cookies = open('./cookies.txt', 'r').readlines()[0]
    headers = {
        'Accept': '*/*',
        'Referer': 'http://weibo.com/minipublish',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': cookies
    }
    # 将数据追加到图片数据的结尾
    fim = open('./mini.png', 'rb').read()
    fim = fim + data
    files = { 'pic1': fim }
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php?cb=http%3A%2F%2Fweibo.com%2Faj%2Fstatic%2Fupimgback.html%3F_wv%3D5%26callback%3DSTK_ijax_14972685830696&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog&s=rdxt'
    result = requests.post(url, files=files, headers=headers, allow_redirects=False)
    # 解析结果
    pid = ''
    if (result.status_code == 302 or result.status_code == 301):
        location = result.headers['location']
        match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
        if (match != None): pid = match.group(1)
    return pid

def UploadImage4(fname):
    cookies = open('./cookies.txt', 'r').readlines()[0]
    headers = {
        'Accept': '*/*',
        'Referer': 'http://weibo.com/minipublish',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': cookies
    }
    
    files = {
        'pic1': open(fname, 'rb')
    }
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php?cb=http%3A%2F%2Fweibo.com%2Faj%2Fstatic%2Fupimgback.html%3F_wv%3D5%26callback%3DSTK_ijax_14972685830696&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog&s=rdxt'
    result = requests.post(url, files=files, headers=headers, allow_redirects=False)
    return result

def UploadImage3(fname):
    cookies = open('./cookies/cookies.txt', 'r').readlines()[0]
    headers = {
        'Cache-Control': 'max-age=0',
        'Origin': 'http://weibo.com',
        'Upgrade-Insecure-Requests': 1,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'http://weibo.com/minipublish',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        
        'Referer': 'http://weibo.com/ttarticle/p/editor',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': 'SINAGLOBAL=5043845025643.67.1486656798299; ULV=1496152980644:4:1:1:4445471441154.32.1496152980234:1489914570957; un=adodo1@126.com; UOR=,,www.takefoto.cn; SCF=AonUlJ-_p5OhCj6zCLC6AcofvbmmK3AfObyCGWgE9dvIObfJWtXzGRjjdZpTktwRI_Z4yz26kGeBgFGvgSp8FJw.; SUB=_2A250ONTKDeRhGedG6FEQ9ynEwziIHXVXTEECrDV8PUNbmtBeLVPRkW9hGgeBzyps-BjnzJ9dCenhm__ugw..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5nBdN4N6.4R3BhsaqYrE8a5JpX5KMhUgL.Fo2Re0epS0MR1hB2dJLoI7XLxKnLBoBL1hU2dXxa; SUHB=0z1B6G5UTJMh7J; ALF=1528682522; SSOLoginState=1497146522'
    }
    
    files = {
        'pic1': open(fname, 'rb')
    }
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php?mime=image%2Fjpeg&marks=1&app=miniblog&url=0&markpos=1&logo=&nick='
    result = requests.post(url, files=files, headers=headers)
    return result


def UploadImage2(fname):
    cookies = open('./cookies/cookies.txt', 'r').readlines()[0]
    headers = {
        'Referer': 'http://weibo.com/ttarticle/p/editor',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'Cookie': cookies
    }
    
    files = {
        'pic1': open(fname, 'rb')
    }
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php?mime=image%2Fjpeg&marks=1&app=miniblog&url=0&markpos=1&logo=&nick='
    result = requests.post(url, files=files, headers=headers)
    return result


def UploadImage1(fname):
    url = 'http://picupload.service.weibo.com/interface/pic_upload.php'
    #url = 'http://httpbin.org/post'
    cookies = open('./cookies/cookies.txt', 'r').readlines()[0]
    mdata = {
        'mime': 'image%2Fjpeg',
        'data': 'base64',
        'url': 0,
        'markpos': 1,
        'logo': '',
        'nick': 0,
        'marks': 1,
        'app': 'miniblog'
    }
    fdata = {
        'file': open(fname, 'rb')
    }
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Cache-Control':'max-age=0',
        'Origin':'http://weibo.com',
        'Referer':'http://weibo.com/minipublish',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'cookie': cookies,
    }
    print cookies
    print '-------------------------'
    #session = requests.session()
    result = requests.post(url, files=fdata, data=mdata, headers=headers)
    return result

def request_image_url(image_path):
    cookie = cookielib.MozillaCookieJar()
    cookie.load(cookie_file, ignore_expires=True, ignore_discard=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    image_url = 'http://picupload.service.weibo.com/interface/pic_upload.php?mime=image%2Fjpeg&data=base64&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog'
    b = base64.b64encode(file(image_path).read())
    data = urllib.urlencode({'b64_data': b})
    result = opener.open(image_url, data).read()
    result = re.sub(r"<meta.*</script>", "", result)
    image_result = json.loads(result)
    image_id = image_result.get('data').get('pics').get('pic_1').get('pid')
    return 'http://ww3.sinaimg.cn/large/%s' % image_id


if __name__ == '__main__':
    #
    print '[==DoDo==]'
    print 'sina disk.'
    print 'Encode: %s' %  sys.getdefaultencoding()

    '''
    #r = UploadImage1('./data/mini.png')
    r = UploadImage4('./out.png')
    if (r.status_code == 302 or r.status_code == 301):
        location = r.headers['location']
        match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
        if (match != None): pid = match.group(1)
        else: pid = ''
        print 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
    '''

    
    # 上传测试
    f = open('./data.zip', 'rb')
    data = f.read()
    f.close()
    #print UploadData3(data)
    UploadData2(data)
    #print 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
    

    '''
    # 断点下载测试
    r = DownloadData_test1()
    d = r.raw.read()
    f = open('ss.rar', 'wb')
    f.write(d)
    f.close()
    '''

    #download_file('')
    #support_continue('http://ww1.sinaimg.cn/large/6d44131cgy1fgjld5vsqvj2001001qv7.jpg')
    print 'ok'
    
