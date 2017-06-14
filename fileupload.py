#!/usr/bin/env python
# encoding: utf-8

import os, sys, math, requests, cookielib, urllib2, urllib, re

def UploadImage4(fname):
    cookies = open('./cookies/cookies.txt', 'r').readlines()[0]
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
    #r = UploadImage1('./data/mini.png')
    r = UploadImage4('./data/test.jpg')
    if (r.status_code == 302 or r.status_code == 301):
        location = r.headers['location']
        match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
        if (match != None): pid = match.group(1)
        else: pid = ''
        print 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
        
