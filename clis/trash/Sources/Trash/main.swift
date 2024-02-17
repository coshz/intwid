/*
 Desc:      A commandline tool to remove file to ~/trash.
 Author:    Coshz fsinhx<AT>gmail.com"
 License:   GLWT(Good Luck With That)
 */

import Foundation
import AppKit

let  __version__ = "0.1.1"
let __author__ = "Coshz fsinhx<AT>gmail.com"


class TrashCL {
    
    var prog: String;
    var args: [String];
    
    init(args args_: [String]){
        prog = args_[0]
        args = Array(args_[1...])
    }
    
    func run(){
        var parsed_args: [String] = [];
        var isrec = true
        for arg in self.args{
            if arg.hasPrefix("-") {
                switch (arg) {
                case "-h", "--help": help(); exit(0)
                case "-y": isrec = false
                case "-v", "--version": print(__version__)
                default:
                    print("Not supported flag `\(arg)`. See `\(prog) -h` for usage.");
                    exit(-1)
                }
            }
            else {
                parsed_args.append(arg)
            }
        }
        remove(paths:parsed_args, isrec)
    }
    
    func remove(paths: [String], _ isrec: Bool){
        let fm = FileManager.default
        for arg in paths{
            if fm.fileExists(atPath: arg){
                do{
                    if(isrec){
                        try fm.trashItem(at: URL(fileURLWithPath: arg), resultingItemURL:nil)
                    } else {
                        try fm.removeItem(at: URL(fileURLWithPath: arg))
                    }
                } catch {
                    print("\(error).")
                }
            }
        }
    }
    
    func help(){
        var h = "Trash \(__version__)\n\(__author__)\n\n";
        h += "Usage: \(self.prog) [flag] <paths>\n\n"
        h += "Argument:\n"
        h += "  <paths>               paths of files/directories to remove.\n\n"
        h += "Optional:\n"
        h += "  -h --help             see help.\n"
        h += "  -v --version          see version.\n"

        print(h)
        exit(0)
    }
}


let tcl = TrashCL(args: CommandLine.arguments)
tcl.run()
