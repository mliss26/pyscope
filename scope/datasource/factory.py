from importlib import import_module
import os
from pathlib import Path
import re

class DataSourceFactory:
    '''Factory for creating concrete ScopeDataSource instances.'''

    def __init__(self):
        self._datasources = {}

        ds_re = re.compile(r'class\s+(\w+)\s*\(\s*ScopeDataSource.*')
        ds_path = Path(os.path.dirname(__file__))
        this_file = os.path.basename(__file__)
        ignore_files = ['__init__.py', this_file, 'scopedatasource.py']

        for file_path in ds_path.glob('*.py'):
            file = os.path.basename(file_path)
            if file in ignore_files:
                continue

            with open(file_path, 'r') as fp:
                module = None
                for line in fp:
                    m = ds_re.search(line)
                    if m:
                        if module is None:
                            module = import_module(f'.{file.split(".py")[0]}', 'scope.datasource')
                        ds_class = m[1]
                        self._datasources[ds_class] = getattr(module, ds_class)

    def list_data_sources(self):
        '''Return list of available data sources.'''
        return list(self._datasources.keys())

    def add_parsers(self, subparser):
        '''Add argument parsers for all available data sources.'''
        for ds in self._datasources.values():
            parser = ds.add_parser(subparser)
            parser.set_defaults(ds_class=ds)
