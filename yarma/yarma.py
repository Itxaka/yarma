from time import sleep
import warnings
import eventlet
import uuid
from oslo_log import log as logging
from os.path import expanduser
from oslo_context import context
from oslo_service import service
from oslo_config import cfg
import oslo_messaging as messaging
eventlet.monkey_patch()


warnings.simplefilter(action='ignore', category=FutureWarning)

register_opts = [
    cfg.StrOpt("transport_url"),
    cfg.StrOpt("consumer_queue", default="yarma"),
    cfg.StrOpt("publisher_queue", default="yarma"),
    cfg.IntOpt("heartbeat_timeout", default=60),
    cfg.BoolOpt("debug", default=False)
]
# register oslo.config options
cfg.CONF.register_opts(register_opts, "default")
cfg.CONF.register_cli_opt(
    cfg.StrOpt("listener",
               choices=["publisher", "consumer"],
               ignore_case=True,
               required=True,
               help="Either publisher or consumer")
)
# register default logging options
logging.register_options(cfg.CONF)

# load config from file
config_file = expanduser("~/.yarma.conf")
cfg.CONF(project="yarma", version="1.1.1", default_config_files=[config_file])

# setup the logger
LOG = logging.getLogger(__name__)
logging.set_defaults(default_log_levels=logging.get_default_log_levels())
logging.setup(cfg.CONF, "yarma")


class YarmaEndpoint(object):
    """This will be attached to the consumer and each message received will be checked
    against the endpoints to see if they respond to that method. In the case that the endpoint
    has the method being called on the incoming message, it will be triggered"""
    def test(self, context, **kwargs):
        LOG.info("Got message {}".format(context["uuid"]))
        return


class YarmaRequestContext(context.RequestContext):
    def __init__(self):
        super(YarmaRequestContext, self).__init__()
        self.uuid = uuid.uuid1()

    def to_dict(self):
        context = {"uuid": self.uuid}
        return context


class YarmaConsumerService(service.Service):
    def __init__(self, transport):
        super(YarmaConsumerService, self).__init__()
        self.consumer_target = messaging.Target(
            topic=cfg.CONF.default.consumer_queue,
            server="rabbit"
        )
        self.transport = transport
        self.server = None

    def start(self):
        self.server = messaging.get_rpc_server(
            self.transport,
            self.consumer_target,
            endpoints=[YarmaEndpoint()],
            executor='threading',
            serializer=messaging.JsonPayloadSerializer()
        )
        self.server.start()

    def stop(self, graceful=False):
        try:
            self.server.stop()
        except Exception:
            pass
        super(YarmaConsumerService, self).stop(graceful)

    def wait(self):
        try:
            self.server.wait()
        except Exception:
            pass
        super(YarmaConsumerService, self).wait()


class YarmaPublisherService(service.Service):
    def __init__(self, transport):
        super(YarmaPublisherService, self).__init__()
        self.publisher_target = messaging.Target(
            topic=cfg.CONF.default.publisher_queue,
        )
        self.transport = transport
        self.server = None
        self.running = False

    def start(self):
        self.server = messaging.RPCClient(
            self.transport,
            self.publisher_target,
            serializer=messaging.JsonPayloadSerializer()
        )
        context = YarmaRequestContext()
        self.running = True
        while self.running:
            self.server.cast(context, "test")
            LOG.info("Message {} sent".format(context.uuid))
            sleep(10)

    def stop(self, graceful=False):
        self.running = False
        super(YarmaPublisherService, self).stop(graceful)


class RabbitMonitoringAgent:
    def __init__(self):
        conf = cfg.CONF.default

        self.transport = messaging.get_transport(cfg.CONF, url=conf.transport_url)

        LOG.info("Starting")
        LOG.debug("Using transport {}".format(self.transport))
        LOG.debug("Using prefetch: {}".format(
            cfg.CONF.oslo_messaging_rabbit.rabbit_qos_prefetch_count
        ))

    def publisher_start(self):
        launcher = service.ProcessLauncher(cfg.CONF, restart_method="mutate")
        publisher = YarmaPublisherService(self.transport)
        launcher.launch_service(publisher)
        launcher.wait()

    def consumer_start(self):
        launcher = service.ProcessLauncher(cfg.CONF, restart_method="mutate")
        consumer = YarmaConsumerService(self.transport)
        launcher.launch_service(consumer)
        launcher.wait()


if __name__ == "__main__":
    agent = RabbitMonitoringAgent()
    if cfg.CONF.listener == "publisher":
        exit(agent.publisher_start())
    elif cfg.CONF.listener == "consumer":
        exit(agent.consumer_start())
