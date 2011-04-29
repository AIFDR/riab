import unittest
from impact import plugins

DEFAULT_PLUGINS = ('Earthquake Fatality Function',)


class Test_Functions(unittest.TestCase):

    def test_get_plugins(self):
        """It is possible to retrieve the list of functions
        """
        plugin_list = plugins.get_plugins()
        msg = ('No plugins were found, not even the built-in ones')
        assert len(plugin_list) > 0, msg

    def test_single_get_plugins(self):
        """Named plugin can be retrieved
        """
        plugin_name = DEFAULT_PLUGINS[0]
        plugin_list = plugins.get_plugins(plugin_name)
        msg = ('No plugins were found matching %s' % plugin_name)
        assert len(plugin_list) > 0, msg


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_Functions, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
