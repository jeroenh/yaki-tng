#!/usr/bin/env python
# encoding: utf-8
"""
Plugin Handling

Created by Rui Carmo on 2006-11-12.
Published under the MIT license.
"""

import os, sys, re, logging, fnmatch, importlib

log = logging.getLogger()

from config import settings
from yaki.core import Singleton


def plugin(cls):
    """Class decorator for adding plugins to the registry"""
    
    Registry().register(cls())
    return cls


class Registry:
    __metaclass__ = Singleton

    plugins    = {'markup': {}}
    registered = []
    serial     = 0
    
    def __init__(self):
        path = os.path.dirname(__file__)
        for f in os.listdir(path):
            if fnmatch.fnmatch(f, "*.py") and (f[0] != '_'):
                (modname,ext) = os.path.basename(f).rsplit('.', 1)
                log.debug("module: %s" % modname)
                try:
                    importlib.import_module('.' + modname,'yaki.plugins')
                except ImportError as e:
                    log.error(e)
                    pass


    def __iter__(self):
        return iter(self.plugins)

        
    def register(self, cls):
        if cls not in self.registered:
            self.registered.append(cls)
        for tag in cls.tags:
            if tag not in self.plugins[cls.category].keys():
                self.plugins[cls.category][tag] = []
            self.plugins[cls.category][tag].append(cls)
        log.debug("Plugin %s registered in category %s for tags %s" % (cls.__class__,cls.category,cls.tags))
    

    def apply_all(self, pagename, soup, request=None, response=None, indexing=False):
        """Runs all markup plugins that process specific tags"""
        for tagname in self.plugins['markup'].keys():
            log.debug(tagname)
            if tagname != 'plugin':
                applicable = self.plugins['markup'][tagname]
                for plugin in applicable:
                    for tag in soup.find_all(tagname):
                        result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
                        self.serial = self.serial + 1
                        if result == True:
                            continue

    def run(self, tag, tagname, pagename = None, soup = None, request=None, response=None, indexing=False):
        if tagname == 'plugin':
            try:
                name = tag['name'].lower() # get the attribute
            except KeyError:
                return
            if name in self.plugins['markup']['plugin']:
                plugin = self.plugins['markup']['plugin'][name]
                if not indexing:
                    result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
                    self.serial = self.serial + 1
                else:
                    tag.replaceWith('')
                # ignore the result for plugin tags
        elif tagname in self.plugins['markup']:
            for i in self.plugins['markup'][tagname]:
                plugin = self.plugins['markup'][tagname][i]
                result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
                self.serial = self.serial + 1
                # if plugin returns False, then the tag does not need to be processed any further
                if result == False:
                    return


class WikiPlugin:
    """Base class for all Wiki plugins"""

    tags = ['plugin']

    def run(self, serial, tag, tagname, pagename, soup, request = None, response = None, indexing = False):
        pass
    
