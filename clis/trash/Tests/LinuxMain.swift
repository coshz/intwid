import XCTest

import trashTests

var tests = [XCTestCaseEntry]()
tests += trashTests.allTests()
XCTMain(tests)
