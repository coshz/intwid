class DragReceiver {
    constructor(logger) {
        var sty = { 
            "width":"100px","height":"100%",
            "position":"fixed",
            "backgroundColor":"green", "opacity": 0.5,
            "display":"none",
        };
        const left_= this.createDroppable("left_for_drag", sty, [0,0,0,undefined]);
        const right_ = this.createDroppable("right_for_drag", sty, [0,undefined,0,0]);
        document.body.appendChild(left_);
        document.body.appendChild(right_);

        this.droppable = [ left_, right_ ];
        this.droppable.forEach((ele) => {
            ele.addEventListener('dragover', (event) => this.handleDragOver(event));
            ele.addEventListener('drop', (event) => this.handleDrop(event));
        });
        this.logger = logger;
    }

    createDroppable(id, sty, pos) {
        var d = document.createElement("div");
        d.id = id;
        ['top','right','bottom','left'].forEach((k,i) => {
            if(pos[i] !== undefined) {
                d.style[k] = pos[i] + "px";
            }
        });
        for(const k in sty) {
            d.style[k] = sty[k];
        }
        return d;
    }

    handleDragOver(event) {
        event.preventDefault();
    }

    async handleDrop(event){
        const idx_photo = event.dataTransfer.getData("Text");
        // const idx_page = idx_photo.replace(/([^ ]+?)(\/in\/[^ ]+)?/g, "$1") + "/sizes/l";
        // console.log(idx_photo);
        // console.log(idx_page);
        let url = "";
        let success = false;
        let retryId = 0;
        while(!success && retryId < 3) {
            try {
                url = await diveUrl(idx_photo);
                success = true;
            } catch (error) {
                this.logger.warn(`${error.message}, trying reconnect (${retryId + 1})...`);
            }
            retryId++;
        }
        if(success) {
            // this.logger.log(`succeed to fetch ${idx_photo}.`);
        } else {
            this.logger.error(`failed to fetch ${idx_photo}.`);
        }
        chrome.runtime.sendMessage({idx: idx_photo, uri: url});
    }

    show() {
        this.droppable.forEach((ele) => {
            ele.style.display = 'block';
        });
    }

    hide() {
        this.droppable.forEach((ele) => {
            ele.style.display = 'none';
        });
    }
}

/* To obtain real image url */
async function diveUrl(idx_photo) {
    const idx_page =  idx_photo.replace(/([^ ]+?)(\/in\/[^ ]+)?/g, "$1") + "/sizes/l";
    return fetch(idx_page)
      .then(response => {
        if(response.ok) {
            return response.text();
        } else {
            throw new Error(`${response.status}: ${response.statusText}`);
        }
      })
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html,"text/html");
        const ol = doc.querySelector("ol.sizes-list");
        const fir = ol.parentElement.firstElementChild;
        if(ol) {
            if(fir.tagName == 'A') {
                return fir.href;
            } else {
                var atags = ol.querySelectorAll("a");
                return atags[atags.length - 1].href;
            }
        } else { 
            throw new Error("image url expected");
        }
      })
      .then(url => fetch(url))
      .then(response => {
        if(response.ok) {
            return response.text();
        } else {
            throw new Error(`${response.status}: ${response.statusText}`);
        }
      })
      .then(html => {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html,"text/html");
        var img = doc.querySelector("div#allsizes-photo").querySelector("img");
        if(img) {
            return img.src;
        } else {
            throw new Error('no image found');
        }
      });
}

function main() {
    const drag_receiver = new DragReceiver(console);
    document.ondragstart = function(event) {
        if(event.target.tagName == "A") {
            const idx= event.target.href;
            if(idx.match(/([^ ]+?)(\/photos)(\/[^\/ ]+){2}(\/in\/[^\/ ]+)?\/?/)){
                event.dataTransfer.setData("Text", event.target.href);
                drag_receiver.show();
            }
        } 
    };
    document.ondragend = function(event) {
        drag_receiver.hide();
    };
}

main();
