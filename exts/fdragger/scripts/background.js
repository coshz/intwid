
async function downloadUri(request) {
    chrome.storage.sync.get(['saveto', 'name'], (result) => {
        const savedir = result.saveto || "flickr";
        const name = naming(request, result.name || "$(ori)");
        const download_option = {
            url: request.uri,
            filename: `${savedir}/${name}`,
            conflictAction: 'uniquify'
        };
        chrome.downloads.download(download_option);
    });
}

function naming(request, fname) {
    const reg = /(?:.*)?\/photos\/([^\/]+)\/([^\/]+)(?:\/in\/([^\/]+))?\/?/;
    const [ _, user, photo, album, ...rest ] = request.idx.match(reg);
    const [ori, ext] = request.uri.substring(request.uri.lastIndexOf('/')+1).split('.');
    return fname.replace(/\$\((user|album|photo|ori)\)/g, 
        matched => ({
            "$(user)": user,
            "$(album)": album,
            "$(photo)": photo,
            "$(ori)":ori
        })[matched] + `.${ext}`
    );
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
            downloadUri(request);
            // logger.info("succeed to fetch ${request.idx}.");
        }
    });
}

main();