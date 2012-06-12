import scons_setup
import cache_unpickle
import options_common

if __name__ == '__main__':
    parser = options_common.getCommonParser(str(__file__))

    parser.add_option('--include-nodes', dest = 'includeNodes', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter in by specific scons nodes')

    parser.add_option('--exclude-nodes', dest = 'excludeNodes', metavar = 'REGEX',
        action = 'append', default = [], help = 'Filter out by specific scons nodes')


    # TODO: Here we apply a callback function for each source node in build
