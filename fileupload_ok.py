#!/usr/bin/env python
# encoding: utf-8
import os, io, sys, math, requests, json, re, base64, logging
import time, ctypes, socket, threading, json, Queue, sqlite3, hashlib
from threading import Thread

__mutex = threading.Lock()        # 线程锁


##########################################################################
##########################################################################
##########################################################################
class Worker(Thread):
    # 线程池工作线程 只支持 python 2.7 或以上版本
    worker_count = 0
    def __init__(self, workQueue, resultQueue, timeout = 0, **kwds):
       Thread.__init__(self, **kwds)
       self.id = Worker.worker_count
       Worker.worker_count += 1
       self.setDaemon(True)
       self.workQueue = workQueue
       self.resultQueue = resultQueue
       self.timeout = timeout
       self.start()
     
    def run(self):
        ''' the get-some-work, do-some-work main loop of worker threads '''
        while True:
            try:
                callable, args, kwds = self.workQueue.get(timeout=self.timeout)
                res = callable(*args, **kwds)
                #print "worker[%2d]: %s" % (self.id, str(res))
                self.resultQueue.put(res)
            except Queue.Empty:
                break
            except :
                print 'worker[%2d]' % self.id, sys.exc_info()[:2]

class WorkerPool:
    # 线程池
    def __init__(self, num_of_workers=10, timeout = 1):
        self.workQueue = Queue.Queue()
        self.resultQueue = Queue.Queue()
        self.workers = []
        self.timeout = timeout
        self._recruitThreads(num_of_workers)
    def _recruitThreads(self, num_of_workers):
        for i in range(num_of_workers): 
            worker = Worker(self.workQueue, self.resultQueue, self.timeout)
            self.workers.append(worker)
    def wait_for_complete(self):
        # ...then, wait for each of them to terminate:
        while len(self.workers):
            worker = self.workers.pop()
            worker.join()
            if worker.isAlive() and not self.workQueue.empty():
                self.workers.append(worker)
        #print "All jobs are are completed."
    def add_job(self, callable, *args, **kwds):
        self.workQueue.put((callable, args, kwds))
    def get_result(self, *args, **kwds):
        return self.resultQueue.get(*args, **kwds)


##########################################################################
##########################################################################
##########################################################################
class YunDisk:
    # 云盘 学习借鉴baidu pcs api
    # 块大小 字节
    BLOCK_SIZE = 2 * 1024 * 1024
    # 基础图片
    BASE_DATA = '89504E470D0A1A0A0000000D49484452' \
                '0000000100000001010300000025DB56' \
                'CA00000003504C5445FFFFFFA7C41BC8' \
                '0000000A4944415408D7636000000002' \
                '0001E221BC330000000049454E44AE42' \
                '6082'.decode('hex')
    # 数据头大小
    HEADER_SIZE = len(BASE_DATA)
            
    
    def __init__(self, cookie, conn):
        # 上传才需要cookie
        self._cookie = cookie
        self._conn = conn
        pass

    def Init(self):
        # 初始化
        pass


            
    def _addNewFile(self, fid, fname):
        # 向数据库添加一个新文件信息
        sql = 'select count(*) from FILES where FID=?'
        args = (fid,)
        cu = conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        count = record[0]
        #
        fsize = os.path.getsize(fname)
        fpath, fname = os.path.split(fname)
        fdate = int(time.time())
        flag = 0
        # 
        if (count == 0):
            # 添加一条文件记录
            sql = 'insert into FILES(FID, FNAME, FSIZE, FPATH, FDATE, FLAG) values(?,?,?,?,?,?)'
            args = (fid, fname, fsize, '/', fdate, flag)
            cu.execute(sql, args)
            
        else:
            # 更新记录
            sql = 'update FILES set FID=?, FNAME=?, FSIZE=?, FPATH=?, FDATE=?, FLAG=? where FID=?'
            args = (fid, fname, fsize, '/', fdate, flag, fid)
            cu.execute(sql, args)
        #

        conn.commit()
        cu.close()

    def UploadFile(self, fname):
        # 上传文件 返回文件fid
        # fname: 文件名
        # 计算MD5值
        fid = self._fileMD5(fname)
        # 判断数据库里是否已经有
        if (self._hasFile(fid)): return fid
        # 没有的话创建一条记录和一张文件表
        self._addNewFile(fid, fname)
        
        
        #return self.UploadPart(fname, 0, -1)
        pass

    def UploadPart(self, fname, start, size):
        # 分段上传 返回文件fid
        # fname: 文件名
        # start: 开始位置
        # size: 读取大小
        f = open(fname, 'rb')

        # 获取文件的大小
        f.seek(0, io.SEEK_END)
        fsize = f.tell()
        # 开始位置已经超出文件大小
        if (start >= fsize): return None
        if (fsize == 0): return None
        if (start < 0): return None
        # 允许size小于0
        if (size <= 0): size = fsize
        # 计算结束位置
        # 注意包含开始但是不包含结束 [start, end)
        end = min(fsize, start + size)
        # 跳转到开始位置
        f.seek(start)

        result = { }
        
        while (True):
            #
            index = f.tell()
            if (index >= end): break
            blocksize = self.BLOCK_SIZE     # 本次读取的块大小
            if (index + blocksize > end):
                blocksize = end - index
            
            data = f.read(blocksize)
            msize = len(data)
            # 处理逻辑
            #print index, msize
            pid = self._uploadData(data)
            if (pid != None): result[(index, index+msize)] = pid
            
            # 判断是否继续循环
            #if (msize < blocksize): break

        # 返回上传结果
        return result

    def DownloadFile(self, fid):
        # 下载文件
        pass

    def DownloadPart(self, fid, start, size):
        # 下载流文件 或者下载分段
        pass

    def GetQuota(self):
        # 获取空间大小
        pass

    def GetMeta(self, fid):
        # 获取文件元信息
        pass

    def ListFiles(self):
        # 获取文件列表
        pass

    def Search(self, wd):
        # 搜索文件
        pass

    # -------------------------------------------------------------------
    def _uploadDataBase64(self, data):
        # 上传数据 用Base64的方法
        headers = {
            'Accept': '*/*',
            'Referer': 'http://weibo.com/minipublish',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
            'Cookie': self._cookie
        }
        # 将数据追加到图片数据的结尾
        fulldata = self.BASE_DATA + data
        
        # 
        b64 = base64.b64encode(fulldata)
        files = [('b64_data', ('', b64, ''))]
        
        url = 'http://picupload.service.weibo.com//interface/pic_upload.php?ori=1&mime=image%2Fjpeg&data=base64&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog'

        logging.info('uploading - size:%d' % len(data))
        result = requests.post(url, files=files, headers=headers, allow_redirects=False)
        # 解析结果
        index = result.text.find('{')
        if (index < 0):
            logging.error('uploaded - size:%d' % len(data))
            return None
        jsonstr = result.text[index:]
        jsonobj = json.loads(jsonstr)
        if (jsonobj['code'] != 'A00006'):
            logging.error('uploaded - size:%d' % len(data))
            return None
        else:
            logging.info('uploaded - size:%d pid:%s' % (len(data), pid))
            return jsonobj['data']['pics']['pic_1']['pid']

    def _uploadData(self, data):
        # 普通上传数据
        headers = {
            'Accept': '*/*',
            'Referer': 'http://weibo.com/minipublish',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
            'Cookie': self._cookie
        }
        # 将数据追加到图片数据的结尾
        fulldata = self.BASE_DATA + data
        files = { 'pic1': fulldata }
        url = 'http://picupload.service.weibo.com/interface/pic_upload.php?cb=http%3A%2F%2Fweibo.com%2Faj%2Fstatic%2Fupimgback.html%3F_wv%3D5%26callback%3DSTK_ijax_14972685830696&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog&s=rdxt&ori=1'

        logging.info('uploading - size:%d' % len(data))
        result = requests.post(url, files=files, headers=headers, allow_redirects=False)
        # 解析结果
        pid = ''
        if (result.status_code == 302 or result.status_code == 301):
            location = result.headers['location']
            match = re.match('.*pid=(.*)&?', location, re.IGNORECASE)
            if (match != None): pid = match.group(1)
        # 验证结果
        if (self._validateData(pid, len(fulldata))):
            logging.info('uploaded - size:%d pid:%s' % (len(data), pid))
            return pid
        else:
            logging.error('uploaded - size:%d' % len(data))
            return None

    def _validateData(self, pid, size):
        # 验证数据有效性 主要通过文件大小判断
        if (pid == None or pid == ''): return False
        url = 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
        response = requests.head(url)
        content_len = response.headers['Content-Length']
        if (content_len == None): return False
        content_len = int(content_len)
        return content_len == size
    
    def _fileMD5(self, fname):
        # 计算文件MD5值
        if not os.path.isfile(fname): return None
        fhash = hashlib.md5()
        f = file(fname, 'rb')
        while True:
            b = f.read(8192)
            if not b : break
            fhash.update(b)
        f.close()
        fmd5 = fhash.hexdigest()
        logging.info('md5 - %s: %s', fmd5, fname)
        return fmd5
    
    def _hasFile(self, fid):
        # 判断数据库里是否已经有 如果有而且状态为[100]就跳过
        sql = 'select FLAG from FILES where FID=?'
        args = (fid,)
        cu = conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        cu.close()
        if (record): return record[0] == 100
        else: return False


##########################################################################
##########################################################################
##########################################################################
if __name__ == '__main__':
    #
    print '[==DoDo==]'
    print 'sina disk.'
    print 'Encode: %s' %  sys.getdefaultencoding()

    # 设置日志
    # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
    logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='fileupload.log',
                filemode='w+')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: [%(levelname)s] %(message)s', '%H:%M:%S')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    


    #
    cookie = open('./cookies/cookies.txt', 'r').read()
    conn = sqlite3.connect('_disk.db', check_same_thread = False)
    disk = YunDisk(cookie, conn)





    
    #data = open('data.zip', 'rb').read()

    # 测试BASE64上传
    #pid = disk._uploadDataBase64(data)
    #print pid
    
    # 测试普通上传
    #pid = disk._uploadData(data)
    #print pid

    #上传测试
    #result = disk.UploadFile('./data/data.rar')


    disk.UploadFile('./data/data.rar')
    
    logging.shutdown()
    print 'OK.'

    
