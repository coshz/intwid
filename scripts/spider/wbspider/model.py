import requests
import os
import re
from utils import DownloadHelper, create_logger
from datetime import datetime
from tqdm.auto import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed


class Model:
    _user_api       = "https://m.weibo.cn/api/container/getIndex?containerid=100505{uid}"
    _timeline_api   = "https://m.weibo.cn/api/container/getIndex?containerid=107603{uid}&page={page}"
    _status_api     = "https://m.weibo.cn/statuses/show?id={id}"
    _repost_api     = "https://m.weibo.cn/api/statuses/repostTimeline?id={id}&page={page}"
    _comment_api    = "https://m.weibo.cn/api/comments/show?id={id}&page={page}"
    _picture_apis   = [ "https://wx4.sinaimg.cn/large/{pid}.jpg", "https://wx4.sinaimg.cn/orj360/{pid}.jpg" ]
    
    LOG_NAME    = 'wb'      # logging file
    PIC_FILE    = 'pic.csv'     # picture table of line format `pid,bid,index`
    RESUME_FILE = 'resume.csv'  # failed urls of line format `url,name` 
    OUT_DIR     = 'out/'        # output directory of pictures

    def __init__(self, option):
        self.option = option
        self.user_info = self.get_userinfo_(self.option.uid)
        self.logger = create_logger(self.LOG_NAME)
        self.downloader = DownloadHelper(cookie=option.cookie)
        self.logger.info("Profile << name: %s, #status: %s >>" %
                         (self.user_info['name'], self.user_info['stat']))
        
    @staticmethod
    def fetch_json_(api, kwargs):
        r = requests.get(api.format(**kwargs), timeout=(5,10))
        r.raise_for_status()
        return r.json()
    
    @classmethod
    def get_userinfo_(cls, uid) -> dict:
        user_json = Model.fetch_json_(cls._user_api,{'uid':uid})
        return {
            'uid': uid,
            'name': user_json['data']['userInfo']['screen_name'],
            'stat': user_json['data']['userInfo']['statuses_count'],
        }
    
    def get_pages_(self, page_start, page_end) -> int:
        """return the last fetched page"""
        
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

                # check datetime
                if self.option.st or self.option.et:
                    sj_time = datetime.strptime(sj['mblog']['created_at'], "%a %b %d %H:%M:%S %z %Y")\
                                      .strftime('%Y-%m-%d %H:%M:%S')
                    if self.option.et and self.option.et < sj_time: continue
                    if self.option.st and self.option.st > sj_time: break

                # we're interested in pictures only
                status = { 
                    'bid':  sj['mblog']['bid'],
                    'pics': sj['mblog']['pic_ids']
                }
                if status['pics']: page_statuses.append(status)
            else: 
                for s in page_statuses:
                    pic_fp.write('\n'.join([f"{s['bid']},{i},{pid}" for i,pid in enumerate(s['pics'])]))
                    pic_fp.write('\n')
                continue
            break
        
        pic_fp.close()
        return page_end
    
    def get_pictures_(self, url_paths):
        url_paths = list(url_paths)
        bad_url_paths = list()
        with ThreadPoolExecutor() as executor:
            futures = [ executor.submit(self.downloader.worker_fn, *url_path)
                       for url_path in url_paths ]
            for future in tqdm(as_completed(futures), total=len(url_paths)):
                err, url_path = future.result()
                if err is not None:
                    bad_url_paths.append(url_path)
                    self.logger.debug(f"Exception `{err}` occured when downloading {url_path[0]}")
        return bad_url_paths
    
    # def get_pictures2_(self, url_paths):
    #     url_paths = list(url_paths)
    #     bad_url_paths = list()
    #     with ProcessPoolExecutor() as executor:
    #         iter_res = executor.map(self.downloader.worker_fn, *zip(*url_paths))
    #         for err, url_path in tqdm(iter_res, total=len(url_paths)):
    #             if err is not None:
    #                 bad_url_paths.append(url_path)
    #                 self.logger.debug(f"Exception `{err}` occured when downloading {url_path[0]}")
    #     return bad_url_paths
    
    def process(self):
        """Two phases: 1. resolve pics to `PIC_FILE`; 2. download pics to `OUT_DIR`."""
        out_dir = os.path.join(
            self.option.out if self.option.out else self.OUT_DIR, self.user_info['name'])
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        urls = paths = list()

        if self.option.resume:
            if not os.path.exists(self.RESUME_FILE): 
                self.logger.error("`--resume` is specified but `resume.csv` is not found")
                return
            self.logger.info(f"Loading url-path pairs from file `{self.RESUME_FILE}` ...")
            with open(self.RESUME_FILE,'r') as f:
                parts_  = re.split(re.compile(",|\n"), f.read())
                urls = parts_[0::2]
                paths = parts_[1::2]
        else:
            if not self.option.download: 
                page_max = self.user_info['stat'] // 10 + 1
                page_start = max(self.option.sp, 1)
                page_end = min(self.option.ep, page_max) # 10 statuses per page
                if page_start > page_max:
                    self.logger.error(f"bad args: sp={self.option.sp} is out of range [1,{page_max}]")
                    return 
                self.logger.info('Resolving pictures ...')
                page_last = self.get_pages_(page_start, page_end)
                if page_start <= page_last:
                    self.logger.info(f"page {page_start} ~ {page_last} are fetched")
                else:
                    self.logger.warn('nothing is fetched, please retry')
                self.logger.info("Done.")
                if self.option.resolve: return
            elif not os.path.exists(self.PIC_FILE):
                self.logger.warn("`--download` is specified but `pic.csv` is not found")
                return
            
            self.logger.info(f"Loading url-path pairs from file {self.PIC_FILE} ...")
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

        if not any([
            self.option.resume, self.option.download, self.option.all,
            self.option.sp, self.option.ep,
            self.option.st, self.option.et]): return

        self.logger.info(f'Start to download {len(urls)} pictures.')
        bad_url_paths = self.get_pictures_(zip(urls,paths))
        self.logger.info(f"End: {len(urls)-len(bad_url_paths)} successed, {len(bad_url_paths)} failed.")
        if len(bad_url_paths) > 0:
            with open(self.RESUME_FILE, 'w') as f:
                f.write('\n'.join([','.join(bup) for bup in bad_url_paths])) 
            self.logger.info("all failed images are savd in `resume.csv`, "
                             "please use `--resume` to re-download them.")
        self.logger.info("Done.")