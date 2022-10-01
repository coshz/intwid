import Foundation
import AppKit
import ArgumentParser

struct Trash: ParsableCommand {
    @Argument(help: "files or directories to delete.")
    var paths: [String]
    
    mutating func run() throws {
        let fm = FileManager.default
        for arg in paths{
            if fm.fileExists(atPath: arg){
                do{
                    try fm.trashItem(at: URL(fileURLWithPath: arg), resultingItemURL:nil)
                } catch {
                    print("Unexpected error: \(error).")
                }
            }
        }
    }

}

Trash.main()

