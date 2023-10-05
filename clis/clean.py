#!/usr/bin/python3

""" 
# version: 1.1 
# date: 2023-04-11
# change: check preference; display size of files.
# version: 1.0
# date: 2022-10-03
# author: coshz
# license: GLWT
"""

import os
import argparse

# __prog__ = "uclean"
__version__ = "1.1"
# __info__ = f"{__prog__} {__version__}"

all_dirs="""
~/Library
~/Library/Application Support
~/Library/Application Scripts
~/Library/Caches
~/Library/Saved Application State
~/Library/Containers
~/Library/Group Containers
~/Library/Application Support/CrashReporter
~/Library/WebKit
/Library
/Library/Application Support
/Users/Shared
/private/var/db
""".strip().split('\n')

cfg_dirs="""
/Library/Preferences
~/Library/Preferences
""".strip().split('\n')


def make_parser():
    parser = argparse.ArgumentParser(description="A Nice Remains Cleaner Developed By Coshz.")
    parser.add_argument('-l', '--list', action='store_true', help="list default directories to look up")
    parser.add_argument('-k', '--key', help="list all remains whoso name contain the given `key`")
    parser.add_argument('-d', '--dirs', nargs='+', help="specify directories to look up")
    parser.add_argument('-p', '--prefs', action='store_true', help="keep preference")
    parser.add_argument('-r', '--rm', action='store_true', help="delete remains")
    parser.add_argument('-s', '--strict', action='store_true', help="strict mode (case-sensitive)")
    parser.add_argument('-v', '--version', action='version', version=__version__)
    return parser

class Cleaner:
    def __init__(self, args) -> None:
        self.dirs = self.path(args.dirs, args.prefs)
        self.key = args.key
        self.args = args

    def path(self, dirs=[], cfg_keep=False):
        dirs_dict = dict()
        dirs_dict['data'] = list(map(os.path.expanduser, all_dirs)) if not dirs else dirs
        dirs_dict['cfg'] = list(map(os.path.expanduser, cfg_dirs)) if not cfg_keep else []
        return dirs_dict

    def process(self):
        if self.args.list:
            # print('\n'.join(appdirs))
            print("Directories to look up:"
                  "\n(a) data (total: {}):\n\t{}"
                  "\n(b) cfg (total: {}):\n\t{}".format(
                len(self.dirs['data']), "\n\t".join(self.dirs['data']), 
                len(self.dirs['cfg']), "\n\t".join(self.dirs['cfg'])))
 
        if self.key:
            res = self.lookup(self.key, sum(list(self.dirs.values()), []), self.args.strict)
            res_dict = self.info(res)
            if not res:
                print("All is clean.")
            else:
                print(f"All remains ({len(res)}) as following:")
                for k, v in res_dict.items():
                      print(f"({v['type']}: {v['size']:7.2f} MB)--{v['path']}")
          
                # print(f"\nTotal: {len(res)} remainders.")
                    
                if args.rm:
                    print('\nMoving to trash...')
                    self.remove(res)
                    print('Done.')

    @classmethod
    def lookup(cls, key, dirs, strict=False):
        res = list()
        key = str.lower(key)
        for dir in dirs:
            for it in os.listdir(dir):
                cond = key == it.lower() if strict else key in it.lower()
                if cond:
                    res.append(os.path.join(dir,it))
        return res

    @classmethod
    def get_size(cls, path):
        total = 0
        if os.path.islink(path):
            pass
        elif os.path.isdir(path):
            total = sum([cls.get_size(p) for p in os.scandir(path)])
        else:
            total = os.path.getsize(path)
        return total
    
    @classmethod
    def remove(cls, res, del_fn='utrash'):
        for it in res:
            os.system(f'{del_fn} "{it}"')

    def info(self, paths):
        info_dict = dict()         
        for i, path in enumerate(paths):
            info_dict.update({f"{i}": {
                'path': path, 
                'type': 'l' if os.path.islink(path) else 'f' if os.path.isfile(path) else 'd', 
                'size': self.get_size(path)/1024**2 # MB
            }})
        return info_dict

if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    cleaner = Cleaner(args)
    cleaner.process()

