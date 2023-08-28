import io
import src.sync as sync
from src.sync import *
import unittest
from unittest.mock import mock_open, patch

class TestDirectory(unittest.TestCase):
    def setUp(self):
        print() # fix unittest not breaking line in CLI

    def test_init(self):
        # Test case 1: Check succesful directory creatin
        thisDir = os.path.dirname(__file__)
        path = os.path.join(thisDir, 'testDir1')
        # make sure the directory does not exist
        if os.path.exists(path):
            os.rmdir(path)
        dir_instance = Directory(path)
        self.assertTrue(os.path.isdir(path))
        self.assertEqual(dir_instance.root_path, os.path.abspath(path))
        os.rmdir(path)

class TestSynchronizer(unittest.TestCase):
    def setUp(self):
        print() # fix unittest not breaking line in CLI

        # init the parser
        parser = argparse.ArgumentParser()
        parser.add_argument("--source", default="./tests/testingSourceDir", type=str, help="Path to the source directory to be mirrored")
        parser.add_argument("--replica", default="./tests/testingReplicaDir", type=str, help="Pyth to the copy of the source directory")
        parser.add_argument("--logDir", default="testingLogDir", type=str, help="Directory where to store the log file")
        parser.add_argument("--logFileName", default="sync.log", type=str, help="Name of the log file")
        parser.add_argument("--syncPeriod", default=5, type=int, help="Time interval in seconds between periodic synchronizations")
        global args
        args = parser.parse_args([])
        sync.args = args

        # init the Synchronizer object
        self.source = Directory ( args.source )
        self.replica = Directory ( args.replica )
        self.synchronizer = Synchronizer(self.source, self.replica)
        thisDir = os.path.dirname(__file__)
        path = os.path.join(thisDir, args.logDir)
        try:
            os.mkdir(path)
        except OSError:
            pass
        with open(os.path.join(path, args.logFileName), 'w') as f:
            f.write('hello world')

    def tearDown(self):
        if os.path.exists(self.source.root_path):
            shutil.rmtree(self.source.root_path)
        if os.path.exists(self.replica.root_path):
            shutil.rmtree(self.replica.root_path)
    
    def test_sanitizeDirs(self):
        # Test case 1: the destination directory does not exist
        self.assertTrue(self.synchronizer._sanitizeDirs(self.source.root_path, self.replica.root_path))
        self.assertTrue(os.path.isdir(self.replica.root_path))

        # Test case 2: the source directory does not exist
        os.rmdir(self.source.root_path)
        self.assertFalse(self.synchronizer._sanitizeDirs(self.source.root_path, self.replica.root_path))
        self.assertFalse(os.path.isdir(self.replica.root_path))

    def test_mirror(self):
        # Test case 1: source and replica directories are identical
        with open(os.path.join(self.source.root_path, 'testFile1.txt'), 'w') as f:
            f.write('hello world')
        shutil.copy(os.path.join(self.source.root_path, 'testFile1.txt'), self.replica.root_path)
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertTrue(os.path.exists(os.path.join(self.replica.root_path, 'testFile1.txt')))

        # Test case 2: source directory has files not present in replica directory
        with open(os.path.join(self.source.root_path, 'testFile2.txt'), 'w') as f:
            f.write('hello world')
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertTrue(os.path.exists(os.path.join(self.replica.root_path, 'testFile2.txt')))

        # Test case 3: replica directory has files not present in source directory
        os.remove(os.path.join(self.source.root_path, 'testFile1.txt'))
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertFalse(os.path.exists(os.path.join(self.replica.root_path, 'testFile1.txt')))

        # Test case 4: source file was modified
        with open(os.path.join(self.source.root_path, 'testFile2.txt'), 'a') as f:
            f.write('appending text')
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertTrue(filecmp.cmp(os.path.join(self.replica.root_path, 'testFile2.txt'), os.path.join(self.source.root_path, 'testFile2.txt')))

        # Test case 5: replica file was modified
        with open(os.path.join(self.replica.root_path, 'testFile2.txt'), 'a') as f:
            f.write('appending different text')
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertTrue(filecmp.cmp(os.path.join(self.replica.root_path, 'testFile2.txt'), os.path.join(self.source.root_path, 'testFile2.txt')))

        # Test case 5: replica dir was deleted
        shutil.rmtree(self.replica.root_path)
        self.synchronizer._mirror(self.source.root_path, self.replica.root_path)
        self.assertTrue(filecmp.cmp(os.path.join(self.replica.root_path, 'testFile2.txt'), os.path.join(self.source.root_path, 'testFile2.txt')))

    def test_copy(self):
        # Test case 1: Copying a file
        with open(os.path.join(self.source.root_path, 'testFile3.txt'), 'w') as f:
            f.write('hello')
        self.synchronizer._copy(['testFile3.txt'], self.source.root_path, self.replica.root_path, self.synchronizer.copyMsg)
        self.assertTrue(os.path.exists(os.path.join(self.replica.root_path, 'testFile3.txt')))

        # Test case 2: Copying a directory
        os.makedirs(os.path.join(self.source.root_path, 'testDir1'))
        self.synchronizer._copy(['testDir1'], self.source.root_path, self.replica.root_path, self.synchronizer.copyMsg)
        self.assertTrue(os.path.exists(os.path.join(self.replica.root_path, 'testDir1')))

    def test_delete(self):
        # Test case 1: Deleting a file
        with open(os.path.join(self.source.root_path, 'testFile4.txt'), 'w') as f:
            f.write('hi')
        self.synchronizer._delete(['testFile4.txt'], self.source.root_path, self.synchronizer.deleteMsg)
        self.assertFalse(os.path.exists(os.path.join(self.source.root_path, 'testFile4.txt')))

        # Test case 2: Deleting a directory
        os.makedirs(os.path.join(self.source.root_path, 'testDir2'))
        self.synchronizer._delete(['testDir2'], self.source.root_path, self.synchronizer.deleteMsg)
        self.assertFalse(os.path.exists(os.path.join(self.source.root_path, 'testDir2')))

    @patch('builtins.open', mock_open())
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_log(self, mock_stdout):
        # Test case 1: Logging a copy operation
        self.synchronizer._log(self.synchronizer.copyMsg, 'srcPath', 'dstPath', False)
        self.assertIn(self.synchronizer.copyMsg, mock_stdout.getvalue())

        # Test case 2: Logging a delete operation 
        self.synchronizer._log(self.synchronizer.deleteMsg, 'srcPath', None, False)
        self.assertIn(self.synchronizer.deleteMsg, mock_stdout.getvalue())

        # Test case 3: Logging an update operation
        self.synchronizer._log(self.synchronizer.updateMsg, 'srcPath', 'dstPath', False)
        self.assertIn(self.synchronizer.updateMsg, mock_stdout.getvalue())

        # Test case 4: Logging a create operation
        self.synchronizer._log(self.synchronizer.createMsg, 'srcPath', None, False)
        self.assertIn(self.synchronizer.createMsg, mock_stdout.getvalue())

        # Test case 5: Logging a warning
        self.synchronizer._log(self.synchronizer.warningMsg, 'srcPath', None, False)
        self.assertIn(self.synchronizer.warningMsg, mock_stdout.getvalue())

        # Test case 6: Logging an error
        self.synchronizer._log(self.synchronizer.errorMsg, 'srcPath', None, False)
        self.assertIn(self.synchronizer.errorMsg, mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()