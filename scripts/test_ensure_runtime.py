import sys
import tempfile
import unittest
from pathlib import Path
from ensure_runtime import ensure


class RuntimeTests(unittest.TestCase):
    def test_existing_dependencies_need_no_project_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            requirements = Path(__file__).resolve().parent.parent/'requirements.txt'
            result = ensure(root, sys.executable, requirements, install=False)
            self.assertTrue(result['ready'])
            self.assertFalse(result['dependencies_installed_now'])
            self.assertFalse((root/'.ppt-runtime').exists())

    def test_missing_requirements_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(FileNotFoundError):
                ensure(root, sys.executable, root/'absent.txt')
            self.assertFalse((root/'.ppt-runtime').exists())


if __name__ == '__main__':
    unittest.main()
