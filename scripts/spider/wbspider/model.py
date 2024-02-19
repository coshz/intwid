import requests
import os
import re
from datetime import datetime
from tqdm.auto import tqdm
from utils import DownloadHelper, create_logger


class Model:
    _user_api       = "https://m.weibo.cn/api/container/getIndex?containerid=100505{uid}"
    _timeline_api   = "https://m.weibo.cn/api/container/getIndex?containerid=107603{uid}&page={page}"
    _status_api     = "https://m.weibo.cn/statuses/show?id={id}"
    _repost_api     = "https://m.weibo.cn/api/statuses/repostTimeline?id={id}&page={page}"
    _comment_api    = "https://m.weibo.cn/api/comments/show?id={id}&page={page}"
    _picture_apis   = [ "https://wx4.sinaimg.cn/large/{pid}.jpg", "https://wx4.sinaimg.cn/orj360/{pid}.jpg" ]
    
    LOG_NAME    = 'wb'          # logging file
    PIC_FILE    = 'pic.csv'     # picture table of line format `pid,bid,index`
    RESUME_FILE = 'resume.csv'  # failed urls of line format `url,name` 

    def __init__(self, option):
        self.option = option
        self.user_info = self.get_userinfo_(self.option.uid)
        self.logger = create_logger(self.LOG_NAME)
        self.downloader = DownloadHelper(cookie=option.cookie)
        self.logger.info("[%s] << name: %s, #status: %s, #page: %s >>" % (
            self.user_info['uid'],
            self.user_info['name'],
            self.user_info['stat'],
            self.user_info['page']
        ))
        
    @staticmethod
    def fetch_json_(api, kwargs):
        r = requests.get(api.format(**kwargs), timeout=(5,10))
        r.raise_for_status()
        return r.json()
    
    @classmethod
    def get_userinfo_(cls, uid) -> dict:
        def page_max(uid):
            first_page = cls.fetch_json_(cls._timeline_api, {'uid': uid, 'page': 1})
            last_maybe = first_page['data']['cardlistInfo']['total'] // \
                            first_page['data']['cardlistInfo']['autoLoadMoreIndex'] + 1
            last_page = cls.fetch_json_(cls._timeline_api, {'uid': uid, 'page': last_maybe})
            
            if not last_page['ok']: 
                return last_maybe - 1
            elif last_page['data']['cardlistInfo'].get('since_id'):
                return last_maybe + 1
            else: 
                return last_maybe
        
        user_json = Model.fetch_json_(cls._user_api,{'uid':uid})
        return {
            'uid':  uid,
            'name': user_json['data']['userInfo']['screen_name'],
            'stat': user_json['data']['userInfo']['statuses_count'],
            'page': page_max(uid)
        }
    
    def get_pages_(self, page_start, page_end) -> int:
        """return the last fetched page and datetime"""

        # we write the result at the intervals between pages
        pic_fp = open(self.PIC_FILE,'w')
        for page in tqdm(range(page_start, page_end + 1)):
            page_statuses = []
            try:
                piece = self.fetch_json_(self._timeline_api, {'uid': self.option.uid, 'page': page})
            except Exception as e:
                self.logger.warn(f"except {e} occured when fetching page {page}; quit...")
                pic_fp.close()
                return page - 1
            for sj in piece['data']['cards']:
                # skip: top status, vip status
                if sj['profile_type_id'].startswith('proweibotop_') or \
                   sj.get('mblog') is None or \
                   (sj['mblog']['mblog_vip_type'] != 0 and not self.option.vip): continue

                # we're interested in pictures only
                status = { 
                    'bid':  sj['mblog']['bid'],
                    'pics': sj['mblog']['pic_ids']
                }
                if status['pics']: page_statuses.append(status)
            
            for s in page_statuses:
                pic_fp.write('\n'.join([f"{s['bid']},{i},{pid}" for i,pid in enumerate(s['pics'])]))
                pic_fp.write('\n')
        
        pic_fp.close()
        return page_end
    
    def query_datetime_by_page_(self, page, latest=False):
        """return page.et (the smallest created datetime)"""
        p  = self.fetch_json_(self._timeline_api, {'uid': self.option.uid, 'page': page})
        s  = [status for status in p['data']['cards']
            if not status['profile_type_id'].startswith('proweibotop_')]
        assert len(s) > 0, "empty page ???"
        dt = s[0 if latest else -1]['mblog']['created_at']
        return datetime.strptime(dt, "%a %b %d %H:%M:%S %z %Y")\
                       .strftime('%Y-%m-%d %H:%M:%S')

    def query_page_by_datetime_(self, dt):
        """find the page such that: page.st <= dt <= page.et"""
        assert len(dt) == 19, f'`{dt}`: wrong datetime format'
        def compare_(dt, page):
            dt_fn = lambda status:\
                datetime.strptime(status['mblog']['created_at'], "%a %b %d %H:%M:%S %z %Y")\
                        .strftime('%Y-%m-%d %H:%M:%S')
            
            p = self.fetch_json_(self._timeline_api, {'uid': self.option.uid, 'page': page})
            statuses = [status for status in p['data']['cards']
                        if not status['profile_type_id'].startwith('proweibotop_')]
            
            dt_h, dt_l = dt_fn(statuses[0]), dt_fn(statuses[-1])
            assert dt_h >= dt_l, 'Ha ???'

            if dt_h >= dt and dt >= dt_l: return 0
            else: return 1 if dt > dt_h else -1

        page_l, page_h = 1, self.user_info['page']
        while page_l < page_h:
            page_m = (page_l + page_h) // 2
            leg = compare_(dt, page_m)
            if leg == 0: 
                return page_m
            elif leg == 1:
                page_l, page_h = page_m, page_h
            else:
                page_l, page_h = page_l, page_m
        return page_h

    def process(self):
        if not any([self.option.resume, self.option.resolve, self.option.download,
            self.option.all,self.option.sp, self.option.ep,
            self.option.st, self.option.et]): 
                self.logger.info('do nothing.')
                return
        
        out_dir = os.path.join(self.option.out, self.user_info['name'])
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        urls = paths = list()

        # get picture-urls from resolving or loading
        if self.option.resume:
            self.logger.debug('Task: resume')
            if not os.path.exists(self.RESUME_FILE): 
                self.logger.error(
                    f"quit since `{self.RESUME_FILE}` is not found; try `--download`?"
                )
                exit(1)
            self.logger.info(f"loading file `{self.RESUME_FILE}` ...")
            with open(self.RESUME_FILE,'r') as f:
                parts_  = re.split(re.compile(",|\n"), f.read())
                urls = parts_[0::2]
                paths = parts_[1::2]
        else:
            if self.option.download: 
                if not os.path.exists(self.PIC_FILE):
                    self.logger.error(f"quit since `--download` is specified "
                                     f"while `{self.PIC_FILE}` is not found")
                    exit(1)
            else:
                self.logger.info('Task: resolve')
                
                if self.option.sp > self.user_info['page']:
                    self.logger.error(f'page {self.option.sp} out of range')
                    exit(1)

                # for simplicity, I convert range of datetime to range of pages
            
                _ = lambda arg, call_f, default_v: call_f(arg) if arg else default_v
                page_start = max(1,
                    _(self.option.sp, lambda x:x, 0),
                    _(self.option.st, self.query_page_by_datetime_, 0)
                )
                page_end = min(self.user_info['page'],
                    _(self.option.ep, lambda x:x, 1<<30),
                    _(self.option.et, self.query_page_by_datetime_, 1<<30)
                )
                del _

                dt_start = self.query_datetime_by_page_(page_end)
                dt_end   = self.query_datetime_by_page_(page_start,latest=True)
                self.logger.info(f"range to fetch: "
                                 f"page: {page_start} ~ {page_end}; "
                                 f"time: {dt_start} ~ {dt_end}")
                
                page_last = self.get_pages_(page_start, page_end)
                
                if page_last < page_end:
                    if page_last < page_start:
                        self.logger.error('quit since no page is fetched, please retry')
                        exit(1)
                    else:
                        self.logger.warn(f"we stop fetching at page {page_last}"
                                         f"you could specify `--sp {page_last+1}` next time")   
                
                if self.option.resolve:
                    self.logger.info("quit since `--resolve` is specified; "
                                     "you can specify `--download` to download them")
                    return
            
            self.logger.info('Task: download')
            self.logger.info(f"loading file {self.PIC_FILE} ...")
            with open(self.PIC_FILE,'r') as f:
                parts_ = re.split(re.compile(',|\n'),f.read())
                bids_ = parts_[0::3]
                idxs_ = parts_[1::3]
                pids_ = parts_[2::3]
                pic_api_ = self._picture_apis[0 if not self.option.thumbnail else 1]
                urls  = [pic_api_.format(pid=pid) for pid in pids_]
                paths = [os.path.join(out_dir,
                    self.option.fmt.format(name=pids_[i],idx=idxs_[i],bid=bids_[i])+'.jpg')
                for i in range(len(pids_))]  

        # download picture-urls

        self.logger.info(f'start to download {len(urls)} pictures.')
        bad_url_paths = self.downloader.fetch_all(zip(urls,paths))
        self.logger.info(f"end: {len(urls)-len(bad_url_paths)} successed, {len(bad_url_paths)} failed.")
        
        # handle failed urls

        if len(bad_url_paths) > 0:
            with open(self.RESUME_FILE, 'w') as f:
                f.write('\n'.join([','.join(bup) for bup in bad_url_paths])) 
            self.logger.warn("please use `--resume` to re-download failed pictures.")
        else:
            self.logger.debug("clean up temporary files")
            os.remove(self.PIC_FILE)
            if os.path.exists(self.RESUME_FILE): os.remove(self.RESUME_FILE)
            self.logger.info("Done.")
