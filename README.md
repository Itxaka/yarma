# yarma
yet another rabbit monitoring agent


# Configuration

Create a config file at ~/.yarma.conf with at least the following values:

````
[DEFAULT]
transport_url=rabbit://user:pass@host:port/vhost

````

The following values are optional but can be used for extra configuration (all under the DEFAULT section):

 * consumer_queue: (String) name of the queue used by the consumer. Defaults to yarma
 * publisher_queue: (String) name of the queue used by the publisher. Defaults to yarma
 * send_msg_every: (Int) the publisher will send a message every X seconds based on this value. Defaults to 30

Then you can use most of the generic config values for both oslo_messaging_rabbit and logging as provided by openstack.

The following are some examples of config options that are really useful

Under DEFAULT:

 * debug: (Bool) set it to true to see debug logging. Defaults to false
 * default_log_levels: (Set) set it to `AMQP=DEBUG, oslo_messaging=DEBUG` to see the full debug logging of the underlying libs. Defaults to INFO levels for all libs
 * logging_debug_format_suffix: (String) appends to debug logging. Useful to add `%(thread)d` so you can see the different threads on the log
 * log_file: (String) use to redirect all logging to a file instead of stdout.

Under oslo_messaging_rabbit:

 * rabbit_qos_prefetch_count: (Int) number of prefetch messages by a consumer. Usefult for testing different scenarios and to see how prefetching affects consumers. Defaults to 100
 * heartbeat_timeout_threshold: (Int) number of seconds after which the Rabbit broker is considered down if heartbeat’s keep-alive fails. Defaults to 60
 * heartbeat_interval: (Int) How often to send heartbeats for consumer’s connections. Defaults to 1
 * heartbeat_rate: (Int) How often times during the heartbeat_timeout_threshold we check the heartbeat. Defaults to 2


# Agents

yarma has 3 different agents:

 * heartbeat agent: simplest of all, it will create a connection to the rabbit service and send 1 message so the heartbeat thread its started by oslo_messaging. Does nothing else afterwards. Its recommended to set the oslo_messaging and/or AMQP log levels to true to see the actual heartbeat exchange
 * publisher agent: publishes a msg every X seconds to a queue with a uuid and a timestamp in the msg body
 * consumer agent: consumes messages from a queue and print their uuid and timestamp


# Run

  * Install yarma with `python setup.py install`
  * It will create a `yarma` executable
  * Exacute it with the preferred agent (`yarma --launch AGENT`):
    * publisher: launchs a publisher agent
    * consumer: launchs a consumer agent
    * heartbeat: launchs a heartbeat agent
    * all: launchs a consumer and publisher agents
