import argparse
from model import Model


def create_parser():
    parser = argparse.ArgumentParser(description="A weibo spider.")
    parser.add_argument('uid', default='', help="user id")
    parser.add_argument('-o','--out', default='', help="output directory")
    parser.add_argument('-t','--thumbnail', action='store_true', help="obtain thumbnails instead of original pictures")
    parser.add_argument('--all', action='store_true', help="fetch all")
    parser.add_argument('--sp', default=0, type=int, help="specify the start page index")
    parser.add_argument('--ep', default=0, type=int, help="specify the end page index")
    parser.add_argument('--st', default='', help="specify the start datetime `%%Y-%%m-%%d` or `%%Y-%%m-%%d %%H:%%M:%%S`")
    parser.add_argument('--et', default='', help="specify the end datetime `%%Y-%%m-%%d` or `%%Y-%%m-%%d %%H:%%M:%%S`")
    parser.add_argument('--fmt', default='{name}', help="file name format (default '{name}', special variables `bid`/`idx`/`name`)")
    parser.add_argument('--resolve', action='store_true', help="only resolve pictures to `pic.csv`")
    parser.add_argument('--download', action='store_true', help="download in reference to `pic.csv` generated from resolution")
    parser.add_argument('--resume', action='store_true', help="download in reference to `resume.csv` generated from incomplete download")
    parser.add_argument('--cookie', default='', help="specify the cookie file")
    parser.add_argument('--vip', action='store_true',help="not skip vip pictures")
    parser.add_argument('--verbose',action='store_true', help="output in debug mode")
    return parser


if __name__ == "__main__":
    args = create_parser().parse_args()

    # validate args
    assert len(args.st) in [0,10,19] and len(args.et) in [0,10,19] \
        , "incorrect datetime format"
    if len(args.st) == 10: args.st += ' 00:00:01'
    if len(args.et) == 10: args.et += ' 23:59:59'

    Model(args).process()