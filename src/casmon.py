#!/usr/bin/python2
"""
Python module which provides an interface for querying information from the Cassandra nodetool. This script is
intended to be used in combination with the Nagios or Icinga client. The Output format is defined by the Icinga and
Nagios rule sets. (https://www.monitoring-plugins.org/doc/guidelines.html#PLUGOUTPUT)
"""
import argparse
import os
import re
import subprocess
from argparse import RawTextHelpFormatter

# Global warn and crit defaults
DEFAULTS = {
    'status':   {'warn': 0,     'crit': 1},
    'heap':     {'warn': 7000,  'crit': 9000},
    'load':     {'warn': 7000,  'crit': 10000}
}

NODETOOL = os.path.normpath('/applications/cassandra/bin/nodetool')
SHELL = '/bin/sh'

SERVICE_STATUS = {
    'Ok': 0,
    'Warning': 1,
    'Critical': 2,
    'Unknown': 3
}


def casmon():
    options = parse_options()
    action = {
        'gcstats':  collect_gcstats,
        'gossip':   check_gossip,
        'handoff':  check_handoff,
        'heapusage':    check_heapusage,
        'load':     check_load,
        'netstats': collect_netstats,
        'status':   check_status,
        'tpstats':  collect_tpstats
    }
    if hasattr(options, 'warn_level') or hasattr(options, 'crit_level'):
        if options.warn_level is not None and options.crit_level is not None:
            action[options.action](warn_level=options.warn_level, crit_level=options.crit_level)
        if options.warn_level is not None:
            action[options.action](warn_level=options.warn_level)
        if options.crit_level is not None:
            action[options.action](crit_level=options.crit_level)
    action[options.action]()


def collect_gcstats():
    """
    Collect Garbage Collection statistics on the current node.
    """
    res = subprocess.check_output([NODETOOL, 'gcstats'])
    line_columns = res.splitlines()[1].split()
    stats = ['interval', 'max_gc_elapsed', 'total_gc_elapsed', 'stdev_gc_elapsed', 'gc_reclaimed']
    gc_stats = {}

    for i, stat in enumerate(stats):
        gc_stats[stat] = line_columns[i]
    print_status_information('Ok', 'Garbage Collection statistics', **gc_stats)


def check_gossip():
    """
    Check Status of gossip.
    """
    res = subprocess.check_output([NODETOOL, 'statusgossip'])
    if re.search(r'^running', res):
        print_status_information('Ok', 'Gossip is running')
    print_status_information('Critical', 'Gossip is not running')


def check_handoff():
    """
    Check Status of Hinted Handoff (Status of storing future hints on the current node).
    """
    res = subprocess.check_output([NODETOOL, 'statushandoff'])
    if re.search(r'^Hinted handoff is running', res):
        print_status_information('Ok', 'Hinted handoff is running')
    print_status_information('Warning', 'Hinted handoff is not running')


def check_heapusage(warn_level=DEFAULTS['heap']['warn'], crit_level=DEFAULTS['heap']['crit']):
    """
    Collects information about the heap usage on this host.

    :param warn_level: Maximum amount of heap usage, before a warning will be triggered
    :param crit_level: Maximum amount of heap usage, before a critical warning will be triggered
    """
    res = subprocess.check_output([NODETOOL, 'info'])
    heap_regex_result = re.search(r'Heap Memory \(MB\)\s*:\s*([\d,.]+)\s/\s([\d,.]+)', res)
    if heap_regex_result is None:
        print_status_information('Unknown', 'Unable to retrieve heap information')
    heap_usage = float(heap_regex_result.group(1))
    if heap_usage > crit_level:
        print_status_information('Critical', 'node heap usage is very high')
    if heap_usage > warn_level:
        print_status_information('Warning', 'node heap usage is high')
    print_status_information('Ok', 'Heap usage is normal', heap_used=heap_usage)


def check_load(warn_level=DEFAULTS['load']['warn'], crit_level=DEFAULTS['load']['crit']):
    """
    Check load of the current node.
    """
    res = subprocess.check_output([NODETOOL, 'info'])
    load_regex_result = re.search(r'Load\s*:\s*([\d,.]+)\sMiB', res)
    if load_regex_result is None:
        print_status_information('Unknown','Unable to retrieve load information')
    load = float(load_regex_result.group(1))
    if load > crit_level:
        print_status_information('Critical', 'node load is very high')
    if load > warn_level:
        print_status_information('Warning', 'node load is high')
    print_status_information('Ok', 'node load is normal', noad_load_mib=load)


def collect_netstats():
    """
    Collect network statistics on the current node.
    """
    res = subprocess.check_output([NODETOOL, 'netstats'])
    res_lines = res.splitlines()
    message_stats = res_lines[len(res_lines)-3:len(res_lines)]
    type_prefix = ['lm_', 'sm_', 'gm_']
    stats = {}
    for prefix in type_prefix:
        line_columns = message_stats[type_prefix.index(prefix)].split()
        stats[prefix + 'pending'] = line_columns[3]
        stats[prefix + 'completed'] = line_columns[4]
        stats[prefix + 'dropped'] = line_columns[5]
    print_status_information('Ok', 'Netstats', **stats)


def check_status(warn_level=DEFAULTS['status']['warn'], crit_level=DEFAULTS['status']['crit']):
    """
    Collects information about status and availability of the cassandra nodes.

    :param warn_level: Maximum amount of nodes down, before a warning will be triggered
    :param crit_level: Maximum amount of nodes down, before a critical warning will be triggered
    """
    res = subprocess.check_output([NODETOOL, 'status'])
    res_lines = res.splitlines()
    dc_regex_result = re.search(r'^Datacenter:\s([\w\d]+)', res)
    if dc_regex_result is None:
        print_status_information('Unknown', 'Unable to retrieve datacenter information')
    dc = dc_regex_result.group(1)
    nodes_down = 0

    for line in res_lines[5:len(res_lines)-1]:
        status = line[:2]
        if status != 'UN':
            nodes_down += 1
    if nodes_down > crit_level:
        print_status_information('Critical', str(nodes_down) + ' node(s) down', dc=dc)
    if nodes_down > warn_level:
        print_status_information('Warning', str(nodes_down) + ' node(s) down', dc=dc)
    if nodes_down == 0:
        print_status_information('Ok', 'All nodes are up and running', dc=dc)
    print_status_information('Ok', 'Enough nodes are up and running', dc=dc)


def collect_tpstats():
    pass
    """
    res = subprocess.check_output([NODETOOL, 'tpstats'])
    res_lines = res.splitlines()

    tpstats = {}
    print_status_information('Ok', 'Tpstats', **tpstats)    
    """


def parse_options():
    """
    Parse the arguments this script was called with.

    :return: Options as Namespace
    """
    global parser
    parser = argparse.ArgumentParser(
        description='Collect and return monitoring information of cassandra nodes or database.',
        formatter_class=RawTextHelpFormatter    # Enable multiline help Strings
    )

    # help='Gather information and print to stdout'
    subparsers = parser.add_subparsers()
    parser_check = subparsers.add_parser('check', formatter_class=RawTextHelpFormatter)
    parser_check.add_argument(
        '-w', '--warning',
        dest='warn_level',
        type=int,
        required=False,
        help='Display warning status if the specified limit is exceeded'
    )
    parser_check.add_argument(
        '-c', '--critical',
        dest='crit_level',
        type=int,
        required=False,
        help='Display critical status if the specified limit is exceeded'
    )
    parser_check.add_argument(
        'action',
        choices=['status', 'heapusage', 'load'],
        help="""status = Check status of cassandra nodes""" +
             """\nheap = Check heap usage of current node""" +
             """\nload = Check load of current node"""
    )

    parser_status = subparsers.add_parser('status', formatter_class=RawTextHelpFormatter)
    parser_status.add_argument(
        'action',
        choices=['gossip', 'handoff'],
        help="""gossip = Status of gossip""" +
             """\nhandoff = Status of storing future hints on the current node"""
    )

    parser_collect = subparsers.add_parser('collect', formatter_class=RawTextHelpFormatter)
    parser_collect.add_argument(
        'action',
        choices=['netstats', 'gcstats'],
        help="""netstats = Network statistics""" +
             """\ngcstats = Garbage Collection statistics"""
    )
    return parser.parse_args()


def print_status_information(status, msg, **kwargs):
    """
    Prints service status to stdout. Output is formatted according to the Nagios / Icinga formatting rules.
    (https://www.monitoring-plugins.org/doc/guidelines.html#PLUGOUTPUT)

    :param status: Exit status
    :param msg: Service status message
    :param kwargs: Performance data for monitoring
    """
    if status in SERVICE_STATUS:
        code = SERVICE_STATUS[status]
        status_msg = status
    else:
        status_msg = 'Unknown'
        code = SERVICE_STATUS[status_msg]
    kwargs_str = ''
    status_information = status_msg + ': ' + msg
    for k, v in kwargs.iteritems():
        kwargs_str += str(k) + '=' + str(v) + ' '
    if len(kwargs) != 0:
        status_information += ' | ' + kwargs_str
    print(status_information)
    exit(code)


if __name__ == '__main__':
    casmon()
