from abc import ABC, abstractmethod


class ScopeDataSource(ABC):
    '''Abstract base class for a source of data to the scope.'''

    @abstractmethod
    def __init__(self, scope, **kwargs):
        '''Data source constructor

           Must save the reference to the scope and perform any required initialization
           for the data source as well as configure the scope parameters.'''
        pass

    @abstractmethod
    def produce_data(self):
        '''Data production function

           This is where the source of data is provided to the scope. It must be a loop
           which provides one or more samples of data for every channel to the scope via
           calls to scope.add_samples.'''
        pass

    @classmethod
    def add_parser(cls, subparser):
        '''Add a parser for data source specific arguments

           A default is provided which may be overridden in subclasses.'''
        return subparser.add_parser(cls.__name__)
