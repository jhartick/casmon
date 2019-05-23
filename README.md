# casmon

### A Apache Cassandra monitoring plugin for Nagios.

This module gathers performance relevant information from the installed cluster and outputs it according to the Nagios monitoring plugin development guidelines which can be found [here](https://www.monitoring-plugins.org/doc/guidelines.html).

This module utilizes the Cassandra [NodeTool](https://wiki.apache.org/cassandra/NodeTool) CLI utility for querying the cluster. Thus, it requires this utility to be present and accessible on the executing instance. Currently this module only supports a fraction of the available performance data (I did not require any more at the point of writing this plugin), so you probably want to customize/extend it to your needs or just request a new feature. :)
