#!/usr/bin/env python
# encoding: utf-8

import os, sys, math, requests, cookielib, urllib2, urllib


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

