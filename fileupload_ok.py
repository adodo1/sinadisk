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
    #
    HEADER_SIZE = len(BASE_DATA)    # 数据头大小
    OUT_PATH = './download/'        # 下载路径
    MAX_THREADS = 4                 # 最大下载线程
    
    def __init__(self, cookie, conn):
        # 上传才需要cookie
        self._cookie = cookie
        self._conn = conn
        pass

    def Init(self):
        # 初始化
        if os.path.exists(self.OUT_PATH) == False:
            os.makedirs(self.OUT_PATH)
        pass

    def UploadFile(self, fname):
        # 上传文件 返回文件fid
        # fname: 文件名
        # 计算MD5值
        fid = self._fileMD5(fname)
        # 判断数据库里是否已经有
        if (self._hasFile(fid)): return fid
        # 没有的话创建一条记录和一张文件表
        self._addNewFile(fid, fname)
        #
        return self.UploadPart(fid, fname, 0, -1)
        

    def UploadPart(self, fid, fname, start, size):
        # 分段上传 返回文件fid
        # fname: 文件名
        # start: 开始位置
        # size: 读取大小

        if (fid == None or fid == ''): return None
        # 加上逻辑 如果没有文件块表创建
        
        
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

        #
        #result = {
        #    'fid': '',
        #    'blocks': [
        #        {'pid': '', 'range':[0, 100], 'error': '', 'head': 82},
        #        {'pid': '', 'range':[100, 200], 'error': '', 'head': 82}
        #    ]
        #}
        result = {
            'fid': fid,
            'fsize': fsize,
            'blocks': [ ]
        }

        num = 0
        count = math.ceil(size * 1.0 / self.BLOCK_SIZE)
        while (True):
            #
            num += 1
            index = f.tell()
            if (index >= end): break
            blocksize = self.BLOCK_SIZE     # 本次读取的块大小
            if (index + blocksize > end):
                blocksize = end - index
            
            data = f.read(blocksize)
            msize = len(data)
            
            # 处理逻辑 print index, msize
            # --------------------------------------------------------------
            # 先判断数据库里是否已经有上传好的数据
            # 如果已经有上传跳过
            block = self._hasPart(fid, index, index + msize)
            if (block != None):
                result['blocks'].append(block)
                continue

            #
            logging.info('uploading - [%d/%d] fid:%s [%d, %d]' % (num, count, fid, index, index+msize))
            pid = self._uploadData(data)
            if (pid != None):
                # 成功
                block = {'pid': pid, 'range':[index, index+msize], 'error': '', 'head': self.HEADER_SIZE}
                result['blocks'].append(block)
                self._insertPart(fid, pid, index, index+msize, self.HEADER_SIZE, 100)   # 插入数据库
            else:
                # 失败
                block = {'pid': '', 'range':[index, index+msize], 'error': 'upload fail.', 'head': self.HEADER_SIZE}
                result['blocks'].append(block)
                self._insertPart(fid, '', index, index+msize, self.HEADER_SIZE, 0)      # 插入数据库
            
            # --------------------------------------------------------------

        # 返回上传结果
        return result

        


    def DownloadFile(self, fid, fast=False):
        # 下载文件
        # fid: 文件FID
        # fast: 使用多线程下载
        fileinfo = self._fileInfo(fid)
        if (fileinfo == None): return None
        fname = fileinfo['name']
        fsize = fileinfo['size']
        fpath = fileinfo['path']
        fdate = fileinfo['date']
        flag = fileinfo['flag']

        writer = open(self.OUT_PATH + fname, 'wb')
        tasks = self.DownloadPart(writer, fid, 0, -1, fast)
        writer.flush()
        writer.close()

        return tasks


    def DownloadPart(self, writer, fid, start, size, fast=False):
        # 下载流文件 或者下载分段
        # fid: 文件FID
        # start: 开始偏移量
        # size: 小于0返回数据到结束
        # fast: 使用多线程下载
        
        #result = [
        #    {'pid': '', 'range': [0, 100], 'head': 82},
        #    {'pid': '', 'range': [100, 200], 'head': 82}
        #         ]
        # 先从数据库取出数据
        if (size == 0): return None
        if (size < 0): end = -1
        else: end = start + size
        blocks = self._fetchData(fid, start, end)
        
        # 检查数据完整性构造下载队列
        tasks = self._buildDownloadTask(blocks, start, end)
        if (tasks == None): return None
        
        # 下载并且放到输出流中 --
        if (fast == False): self._doTasks(fid, tasks, writer, 4096)
        else: self._doTasksFast(fid, tasks, writer, 4096)
        
        #
        return tasks

            


    def GetQuota(self):
        # 获取空间大小
        pass

    def GetMeta(self, fid):
        # 获取文件元信息
        fileinfo = self._fileInfo(fid)
        return fileinfo

    def ListFiles(self):
        # 获取文件列表
        filelist = self._fileList()
        return filelist

    def Search(self, wd):
        # 搜索文件
        pass



    # -------------------------------------------------------------------
    # -------------------------------------------------------------------
    # -------------------------------------------------------------------
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
        fmd5 = fhash.hexdigest().lower()
        logging.info('md5 - %s: %s', fmd5, fname)
        return fmd5
    
    def _hasFile(self, fid):
        # 判断数据库里是否已经有 如果有而且状态为[100]就跳过
        sql = 'select FLAG from FILES where FID=?'
        args = (fid,)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        cu.close()
        if (record): return record[0] == 100
        else: return False
        
    def _addNewFile(self, fid, fname):
        # 向数据库添加一个新文件信息
        sql = 'select count(*) from FILES where FID=?'
        args = (fid,)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        count = record[0]
        #
        fsize = os.path.getsize(fname)
        fpath, fname = os.path.split(fname)
        fdate = int(time.time())
        flag = 0
        ftable = '_' + fid
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
        # 创建文件块信息表
        sql = """
                CREATE TABLE IF NOT EXISTS [{0}] (
                  [PID] CHAR(40), 
                  [FSTART] INT, 
                  [FEND] INT, 
                  [HEADSIZE] INT, 
                  [PDATE] INT, 
                  [FLAG] INT)
              """.format(ftable)
        cu.execute(sql)
        #
        self._conn.commit()
        cu.close()
        
    def _hasPart(self, fid, start, end):
        # 判断数据库里是否已经有 如果有而且状态为[100]就跳过
        ftable = '_' + fid
        sql = 'select PID, FSTART, FEND, HEADSIZE, PDATE, FLAG from {0} where FSTART=? and FEND=?'.format(ftable)
        args = (start,end)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        cu.close()

        if (record):
            pid = record[0]
            start = record[1]
            end = record[2]
            headsize = record[3]
            pdate = record[4]
            flag = record[5]
            if (flag == 100):
                block = {'pid': pid, 'range':[start, end], 'error': '', 'head': headsize}
                return block
        # 否则返回空
        return None
        
    def _insertPart(self, fid, pid, start, end, headsize, flag):
        # 插入块信息
        ftable = '_' + fid
        pdate = int(time.time())
        
        sql = 'select FLAG from {0} where FSTART=? and FEND=?'.format(ftable)
        args = (start, end)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        #
        if (record):
            # 更新原有记录
            sql = 'update {0} set PID=?, HEADSIZE=?, PDATE=?, FLAG=? where FSTART=? and FEND=?'.format(ftable)
            args = (pid, headsize, pdate, flag, start, end)
            cu.execute(sql, args)
            self._conn.commit()
        else:
            # 插入新纪录
            sql = 'insert into {0}(PID, FSTART, FEND, HEADSIZE, PDATE, FLAG) values(?,?,?,?,?,?)'.format(ftable)
            args = (pid, start, end, headsize, pdate, flag)
            cu.execute(sql, args)
            self._conn.commit()
        #
        cu.close()

    def _fetchData(self, fid, start, end):
        # 从数据库获取记录
        # 注意 [start, end) 不包含end
        # end 小于0返回到文件末尾
        ftable = '_' + fid
        sql = 'select count(*) from FILES where FID=?'
        args = (fid,)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        if (record[0] == 0): return []

        # 取出记录
        #result = [
        #    {'pid': '', 'range': [0, 100], 'head': 82},
        #    {'pid': '', 'range': [100, 200], 'head': 82}
        #         ]
        result = []
        sql = 'select PID, FSTART, FEND, HEADSIZE, PDATE from {0} where FLAG=100 ' \
              'and (FSTART<? or ?<0) and FEND>=? order by FSTART desc'.format(ftable)
        args = (end, end, start)
        cu.execute(sql, args)
        records = cu.fetchall()
        for row in records:
            # 遍历记录
            pid = row[0]
            fstart = row[1]
            fend = row[2]
            headsize = row[3]
            pdate = row[4]
            block = {'pid': pid, 'range': [fstart, fend], 'head': headsize}
            result.append(block)
        cu.close()
        #
        return result

    def _buildDownloadTask(self, blocks, start, end):
        # 检查 和 构造下载任务
        # 数据必须是连续的 否则返回空
        #tasks = {
        #    'size': 0,
        #    'start': 0,
        #    'tasks': [
        #        {'pid': '', 'index': 0, 'range': [0, 0]},
        #        {'pid': '', 'index': 1, 'range': [0, 0]}
        #    ]
        #}
        tasks = {
            'size': 0,
            'start': start,
            'tasks': [ ]
        }
        # 按照块的开始排序 块必须 收尾相接 否则返回错误
        blocks.sort(key=lambda item:item['range'][0], reverse=False)
        index = 0
        lastbs = 0
        size = 0
        for block in blocks:
            bs = block['range'][0]
            be = block['range'][1]
            pid = block['pid']
            head = block['head']

            # 文件相对偏移量
            offsets = head
            offsete = head + be - bs

            # 算法没有验证过 没有做过仔细检查
            # 计算偏移量 ~乱
            if (be <= start):
                # 1. 不在范围内
                continue
            elif (bs < end):
                # 2. 落在块区间里 计算相对偏移量
                if (bs < start): offsets += start - bs
                if (be > end): offsete -= be - end
            elif (bs >= end):
                # 3. 不在范围内
                pass
            else: 
                # 4. 考虑不周
                raise Exception()

            #
            index += 1
            task = {'pid': pid, 'index': index, 'range': [offsets, offsete]}
            if (lastbs > 0 and lastbs != bs):
                # 数据不连续返回空
                return None
            
            # 添加一条任务
            size += offsete - offsets
            tasks['tasks'].append(task)
            
        tasks['size'] = size
        
        return tasks
    
    def _doTasks(self, fid, tasks, writer, buff):
        # 下载任务
        # tasks: 任务列表
        # writer: 输出流
        # buff: 每隔多少刷新一次
        #tasks = {
        #    'size': 0,
        #    'start': 0,
        #    'tasks': [
        #        {'pid': '', 'index': 0, 'range': [0, 0]},
        #        {'pid': '', 'index': 1, 'range': [0, 0]}
        #    ]
        #}
        # 按照index排序
        size = tasks['size']
        tasklist = tasks['tasks']
        tasklist.sort(key=lambda item:item['index'], reverse=False)
        index = 0
        for task in tasklist:
            # 循环任务
            index = index + 1
            pid = task['pid']
            index = task['index']
            start = task['range'][0]
            end = task['range'][1]
            #
            logging.info('downloading - [%d/%d] pid:%s [%d, %d]' % (index, len(tasklist), pid, start, end))
            
            url = 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
            headers = { 'Range': 'bytes=%d-%d' % (start, end) }
            
            # HTTP 200 获取全部数据
            # HTTP 206 获取部分数据
            
            # 为了保证返回数据正确 尝试3次请求 如果得不到206结果抛出异常
            r = requests.get(url, headers = headers, stream=True)
            if (r.status_code != 206):
                r.close()
                # 第二次请求
                r = requests.get(url, headers = headers, stream=True)
                if (r.status_code != 206):
                    r.close()
                    # 第三次请求
                    r = requests.get(url, headers = headers, stream=True)
                    if (r.status_code != 206):
                        r.close()

            # 读取数据
            if (r.status_code == 200):
                # 返回结果200需要自己过滤有效数据
                index = 0
                for chunk in r.iter_content(chunk_size=buff):
                    # 分块下载
                    if chunk: # filter out keep-alive new chunks
                        size = len(chunk)

                        data = None

                        newstart = 0
                        newend = size

                        # 算法没有验证过 没有做过仔细检查
                        if (end <= index):
                            # 已经结束 不在范围内
                            break
                        elif (start < index+size):
                            # 落在区间内
                            if (start > index): newstart = start - index
                            if (end < index+size): newend = index+size - end
                        elif (start >= index+size):
                            # 还没开始
                            continue
                        else:
                            # 考虑不周
                            raise Exception()
                        
                        data = chunk[newstart : newend]
                        
                        writer.write(data)
                        writer.flush()
                pass
            elif (r.status_code == 206):
                # 返回结果200数据已经过滤好了 直接写入流里
                for chunk in r.iter_content(chunk_size=buff):
                    # 分块下载
                    if chunk: # filter out keep-alive new chunks
                        writer.write(chunk)
                        writer.flush()
                
            
            
                    
            logging.info('downloaded - pid:%s' % pid)

    def _fileInfo(self, fid):
        # 获取文件信息
        sql = 'select FID, FNAME, FSIZE, FPATH, FDATE, FLAG from FILES where FID=?'
        args = (fid,)
        cu = self._conn.cursor()
        cu.execute(sql, args)
        record = cu.fetchone()
        cu.close()
        if (record):
            fid = record[0]
            fname = record[1]
            fsize = record[2]
            fpath = record[3]
            fdate = record[4]
            flag = record[5]
            return {'fid': fid, 'name': fname, 'size': fsize, 'path': fpath, 'date': fdate, 'flag': flag}
        else: return None

    def _fileList(self):
        # 获取文件列表
        sql = 'select FID, FNAME, FSIZE, FPATH, FDATE, FLAG from FILES'
        cu = self._conn.cursor()
        cu.execute(sql)
        records = cu.fetchall()
        cu.close()
        results = []
        for row in records:
            fid = row[0]
            fname = row[1]
            fsize = row[2]
            fpath = row[3]
            fdate = row[4]
            flag = row[5]
            item = {'fid': fid, 'name': fname, 'size': fsize, 'path': fpath, 'date': fdate, 'flag': flag}
            results.append(item)
        # 
        return results

    def _doTasksFast(self, fid, tasks, writer, buff):
        # 下载任务
        # fid: 文件FID
        # tasks: 任务列表
        # writer: 输出流
        # buff: 每隔多少刷新一次
        #tasks = {
        #    'size': 0,
        #    'start': 0,
        #    'tasks': [
        #        {'pid': '', 'index': 0, 'range': [0, 0]},
        #        {'pid': '', 'index': 1, 'range': [0, 0]}
        #    ]
        #}
        # 按照index排序
        size = tasks['size']
        tasklist = tasks['tasks']
        tasklist.sort(key=lambda item:item['index'], reverse=False)

        # 初始化多线程
        worker = WorkerPool(self.MAX_THREADS)

        # 1. 下载分块文件
        # 2. 把分块文件拼起来
        
        for task in tasklist:
            # 循环任务
            pid = task['pid']
            index = task['index']
            start = task['range'][0]
            end = task['range'][1]
            
            # 添加任务到线程池里
            worker.add_job(self._downloadBlock, fid, pid, index, start, end)

        # 等待线程结束
        worker.wait_for_complete()

        # 检查和拼接数据
        result = self._unionData(fid, tasklist, writer)
        

    def _unionData(self, fid, tasks, writer):
        # 检查块文件完整性 拼接数据
        for task in tasks:
            pid = task['pid']
            index = task['index']
            #
            blockfile = '%s%s_%05d.block' % (self.OUT_PATH, fid, index)     # 块文件
            if (os.path.exists(blockfile) == False): return False           # 块文件缺少
        # 拼接数据
        for task in tasks:
            pid = task['pid']
            index = task['index']
            #
            blockfile = '%s%s_%05d.block' % (self.OUT_PATH, fid, index)     # 块文件
            f = open(blockfile, 'rb')
            data = f.read()
            f.close()
            writer.write(data)
            writer.flush

            # 删除块文件
            os.remove(blockfile)
        #
        return True

    def _downloadBlock(self, fid, pid, index, start, end):
        # 下载文件分块线程
        url = 'http://ww1.sinaimg.cn/large/{0}.jpg'.format(pid)
        blockfile = '%s%s_%05d.block' % (self.OUT_PATH, fid, index)     # 块文件

        # 如果已经有块文件跳过
        if (os.path.exists(blockfile)): return True

        logging.info('downloading - index:%05d fid:%s pid:%s' % (index, fid, pid))
        
        # 下载文件
        headers = { 'Range': 'bytes=%d-%d' % (start, end) }
        response = requests.get(url, headers=headers, stream=True)
        data = response.raw.read()
        if (response.status_code == 200):
            # 截取有效数据
            data = data[start : end]
        elif (response.status_code == 206):
            # 有效数据
            pass
        else:
            # 返回结果错误
            return False

        # 检查数据长度
        if (len(data) != end - start): return False

        # 数据写入块文件
        f = open(blockfile, 'wb')
        f.write(data)
        f.close()
        return True
        

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
                filemode='a')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: [%(levelname)s] %(message)s', '%H:%M:%S')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    

    # http://weibo.com/minipublish
    
    # 构造函数
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
    #result = disk.UploadFile('./data/MIJIAN3.avi')

    # 测试下载
    #r = disk.UploadFile('./data/test2.avi')
    #r = disk.DownloadFile('8edf97bca7f31f6fbf9e4571f214d558')
    #r = disk.DownloadPart('8edf97bca7f31f6fbf9e4571f214d558', 10, 3*1024*1024)
    #print json.dumps(r)

    #r = disk.DownloadFile('7ae56bde1c88a678a0010004bbf5ff2c', True)
    #print len(r)


    #url = 'http://ww1.sinaimg.cn/large/{0}.jpg'.format('81d9973cgy1fgn6w91rtrj20010011ky')
    #headers = { 'Range': 'bytes=%d-%d' % (82, 100) }
    #r = requests.get(url, headers = headers, stream=True)
    #for data in r.iter_content(chunk_size=10):
    #    print len(data)

    # 测试获取文件列表
    filelist = disk.ListFiles()
    print filelist
    
    
    logging.shutdown()
    print 'OK.'

    
