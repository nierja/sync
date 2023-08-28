#!/usr/bin/python

import argparse
import datetime
import filecmp
import os
import shutil
import sched
import time
from datetime import datetime

# Parser for handling CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--source",
    default="../tests/sourceDir",
    type=str,
    help="Path to the source directory to be mirrored",
)
parser.add_argument(
    "--replica",
    default="../tests/replicaDir",
    type=str,
    help="Destinaton path of the backup (replica) directory",
)
parser.add_argument(
    "--logDir",
    default="../tests/logDir/",
    type=str,
    help="Directory where to store the log file",
)
parser.add_argument(
    "--logFileName", default="sync.log", type=str, help="Name of the log file"
)
parser.add_argument(
    "--syncPeriod",
    default=5,
    type=int,
    help="Time interval in seconds between periodic synchronizations (backups)",
)

def tStamp() -> datetime:
    """Return timestamp in desired format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Functions to return colored text for terminal
def green(text: str) -> str:
    return f"\033[92m{text}\033[00m"
def red(text: str) -> str:
    return f"\033[91m{text}\033[00m"
def yellow(text: str) -> str:
    return f"\033[93m{text}\033[00m"
def blue(text: str) -> str:
    return f"\033[96m{text}\033[00m"
def orange(text: str) -> str:
    return f"\033[33m{text}\033[00m"
def purple(text: str) -> str:
    return f"\033[35m{text}\033[00m"

def cleanTerminal():
    """Clean the terminal for convenience"""
    # Windows
    if os.name == "nt":
        os.system("cls")
    # macOS and Linux
    else:
        os.system("clear")


class Directory:
    """Class representing a directory"""

    def __init__(self, path):
        # if need be, convert relative path to absolute
        thisDir = os.path.dirname(__file__)
        dirName = os.path.join(thisDir, path)
        self.root_path = os.path.abspath(dirName)

        if not os.path.isdir(self.root_path):
            print(f"{blue('[ CREATE ]')}  {tStamp()}  DIR {path}")
            try:
                os.makedirs(dirName)
            except OSError as e:
                print(f"{red('[ ERROR  ]')}  {e.filename} - {e.strerror}")


class Synchronizer:
    """Class for a synchronization object"""

    def __init__(self, source: Directory, replica: Directory):
        self.source = source
        self.replica = replica
        self.successFlag = 1

        self.copyMsg = "[ COPY   ]"
        self.deleteMsg = "[ DELETE ]"
        self.updateMsg = "[ UPDATE ]"
        self.warningMsg = "[ WARN   ]"
        self.errorMsg = "[ ERROR  ]"
        self.createMsg = "[ CREATE ]"

        try:
            shutil.rmtree(args.logDir)
        except OSError:
            pass
        _ = Directory(args.logDir)

    def _sanitizeDirs(self, src, dst):
        """
            Makes sure the directories are either
            accesible for self._mirror() or returns a failiure code

        Args:
            src (string): path to the source directory
            dst (string): path to the replica directory

        Returns:
            bool: success indicator
        """
        if not os.path.isdir(dst):
            if not os.path.isdir(src):
                return not self.successFlag
            self._log(self.createMsg, dst, dst=None, isFile=False)
            try:
                os.makedirs(dst)
                return self.successFlag
            except OSError as e:
                print(f"{red(self.errorMsg)}  {e.filename} - {e.strerror}")

        if not os.path.isdir(src):
            if not os.path.isdir(dst):
                return not self.successFlag
            self._delete(os.listdir(dst), dst, self.deleteMsg)
            self._log(self.deleteMsg, dst, dst=None, isFile=False)
            os.removedirs(dst)
            return not self.successFlag
        return self.successFlag

    def _mirror(self, src, dst):
        """
            This method compares directories and executes one-way mirroring of src into dst

        Args:
            src (string): path to the source directory
            dst (string): path to the replica directory
        """
        # check if src, dst are accesible; if not, exit the function
        success = self._sanitizeDirs(src, dst)
        if not success:
            return
        cmpObject = filecmp.dircmp(src, dst)

        # if src, dst have common subdirs, run _mirror() recursively
        if cmpObject.common_dirs:
            for dir in cmpObject.common_dirs:
                self._mirror(os.path.join(src, dir), os.path.join(dst, dir))

        # file/dir only in src/dst; perform simle copy/deletion
        if cmpObject.left_only:
            self._copy(cmpObject.left_only, src, dst, self.copyMsg)
        if cmpObject.right_only:
            self._delete(cmpObject.right_only, dst, self.deleteMsg)

        # src and dst contain modified version of the same files/dirs
        srcNewer, dstNewer = [], []
        if cmpObject.diff_files:
            for file in cmpObject.diff_files:
                srcTimeModified = os.stat(os.path.join(src, file)).st_mtime
                dstTimeModified = os.stat(os.path.join(dst, file)).st_mtime
                if srcTimeModified > dstTimeModified:
                    srcNewer.append(file)
                else:
                    dstNewer.append(file)
        self._copy(srcNewer, src, dst, self.updateMsg)
        self._copy(dstNewer, src, dst, self.updateMsg)

    def _delete(self, fileList, src, opMsg):
        """
            Delete a list of files in the src directory

        Args:
            fileList (List): List of file paths (string)
            src (string): path to the source directory
            opMsg (string): operation message to be displayed and logged
        """
        for file in fileList:
            srcPath = os.path.join(src, os.path.basename(file))
            if os.path.isdir(srcPath):
                try:
                    shutil.rmtree(srcPath)
                except OSError as e:
                    print(f"{red(self.errorMsg)}  {e.filename} - {e.strerror}")
                self._log(opMsg, srcPath, dst=None, isFile=False)
            else:
                try:
                    os.remove(srcPath)
                except OSError as e:
                    print(f"{red(self.errorMsg)}  {e.filename} - {e.strerror}")
                self._log(opMsg, srcPath, dst=None, isFile=True)

    def _copy(self, fileList, src, dst, opMsg):
        """
            Copy a list of files from src directory to dst directory

        Args:
            fileList (List): List of file paths (string)
            src (string): path to the source directory
            dst (string): path to the replica directory
            opMsg (string): operation message to be displayed and logged
        """
        for file in fileList:
            srcPath = os.path.join(src, os.path.basename(file))
            dstPath = os.path.join(dst, os.path.basename(file))
            if os.path.isdir(srcPath):
                try:
                    shutil.copytree(srcPath, dstPath)
                except OSError as e:
                    print(f"{red(self.errorMsg)}  {e.filename} - {e.strerror}")
                self._log(opMsg, srcPath, dstPath, isFile=False)
            else:
                try:
                    shutil.copy2(srcPath, dst)
                except OSError as e:
                    print(f"{red(self.errorMsg)}  {e.filename} - {e.strerror}")
                self._log(opMsg, srcPath, dst=dstPath, isFile=True)

    def _log(self, op, src, dst=None, isFile=True):
        """
        Log the executed operations to the terminal (colored) and to the log file args.logFileName
        """
        opMsg = op
        match op:
            case self.copyMsg:
                opMsgColor = green(opMsg)
            case self.deleteMsg:
                opMsgColor = orange(opMsg)
            case self.updateMsg:
                opMsgColor = yellow(opMsg)
            case self.createMsg:
                opMsgColor = blue(opMsg)
            case self.warningMsg:
                opMsgColor = red(opMsg)
            case _:
                opMsg = self.errorMsg
                opMsgColor = red(opMsg)

        time = tStamp()
        msgTerm = f"{opMsgColor}  {time}  {'FILE' if isFile else 'DIR '} {src}"
        msgLog = f"{opMsg}  {time}  {'FILE' if isFile else 'DIR '} {src}"
        if op == self.copyMsg:
            msgTerm += f" TO {dst}"
            msgLog += f" TO {dst}"
        print(msgTerm)
        thisDir = os.path.dirname(__file__)
        dirName = os.path.join(thisDir, args.logDir)
        with open(os.path.join(dirName, args.logFileName), mode="a+") as logFile:
            logFile.writelines(msgLog + "\n")


def synchronize(scheduler, synchronizer, src, rpl):
    """
    Run _mirror() method every n=(args.syncPeriod) secons
    """
    scheduler.enter(
        args.syncPeriod, 1, synchronize, (scheduler, synchronizer, src, rpl)
    )
    print(f"[ SYNCHR ]")
    synchronizer._mirror(src, rpl)


def main(args: argparse.Namespace) -> int:
    """
        Utility script for one-way folder synchronization

    Args:
        args (argparse.Namespace): dict of CLI parameters
    """
    # Convenienca preparations
    cleanTerminal()
    thisDir = os.path.dirname(__file__)
    replicaDirName = os.path.join(thisDir, args.replica)
    try:
        shutil.rmtree(replicaDirName)
    except OSError as e:
        pass

    src = Directory(args.source)
    rpl = Directory(args.replica)
    sync = Synchronizer(src, rpl)
    sync._mirror(src.root_path, rpl.root_path)

    # Manage repeated execution of sync._compareDirs() via scheduler
    myScheduler = sched.scheduler(time.time, time.sleep)
    myScheduler.enter(
        args.syncPeriod,
        1,
        synchronize,
        (myScheduler, sync, src.root_path, rpl.root_path),
    )
    myScheduler.run()


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    main(args)
