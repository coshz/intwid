
async function downloadUri(uri) {
    const fname = uri.substring(uri.lastIndexOf('/')+1);
    chrome.storage.sync.get(['saveto'], (result) => {
        const savedir = result.saveto || "flickr";
        const download_option = {
            url: uri,
            filename: `${savedir}/${fname}`,
            conflictAction: 'uniquify'
        };
        chrome.downloads.download(download_option);
    });
}

function createLogger(logger) {
    return {
        getCurrtime_: function() {
            return Date.now().toLocaleString();
        },
        log: function(msg) {
            return logger.log(this.getCurrtime_(), " -- [INFO] ", msg);
        },
        warn: function(msg) {
            return logger.warn(this.getCurrtime_(), " -- [WARNING] ", msg);
        },
        error: function(msg) {
            return logger.error(this.getCurrtime_(), " -- [ERROR] ", msg);
        }
    }
}

function main() {
    let idx_list = [];
    const logger = createLogger(console);
    chrome.runtime.onMessage.addListener(async function (request,sender,sendResponse) {
        if(request.uri === "") {
            logger.error(`failed to fetch ${request.idx}.`);
            idx_list.push(request.idx);
        } else {
            downloadUri(request.uri);
            // logger.info("succeed to fetch ${request.idx}.");
        }
    });
}

main();