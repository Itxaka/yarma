import warnings
import eventlet
import uuid
import datetime
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
    cfg.IntOpt("send_msg_every", default=30)
]
# register oslo.config options
cfg.CONF.register_opts(register_opts, "default")
cfg.CONF.register_cli_opt(
    cfg.StrOpt("launch",
               choices=["heartbeat", "consumer", "publisher", "all"],
               ignore_case=True,
               required=True,
               help="Either heartbeat, consumer, publisher or all")
)
# register default logging options
logging.register_options(cfg.CONF)

# load config from file
config_file = expanduser("~/.yarma.conf")
cfg.CONF(project="yarma", version="1.0.0", default_config_files=[config_file])

# setup the logger
LOG = logging.getLogger(__name__)
logging.set_defaults(default_log_levels=logging.get_default_log_levels())
logging.setup(cfg.CONF, "yarma")

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class YarmaEndpoint(object):
    """This will be attached to the consumer and each message received will be checked
    against the endpoints to see if they respond to that method. In the case that the endpoint
    has the method being called on the incoming message, it will be triggered"""
    def test(self, context, **kwargs):
        timestamp = datetime.datetime.strptime(context["timestamp"], TIME_FORMAT)
        LOG.info("Got message {} with timestamp {}".format(context["uuid"], timestamp))
        return


class YarmaRequestContext(context.RequestContext):
    def __init__(self):
        super(YarmaRequestContext, self).__init__()
        self.uuid = uuid.uuid1()
        self.timestamp = datetime.datetime.utcnow().strftime(TIME_FORMAT)

    def to_dict(self):
        return {"uuid": self.uuid, "timestamp": self.timestamp}


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


class YarmaHearbeatService(service.Service):
    def __init__(self, transport):
        super(YarmaHearbeatService, self).__init__()
        self.publisher_target = messaging.Target(
            topic=cfg.CONF.default.publisher_queue,
        )
        self.transport = transport
        self.server = messaging.RPCClient(
            self.transport,
            self.publisher_target,
            serializer=messaging.JsonPayloadSerializer()
        )

    def start(self):
        # send a msg so the connection gets established and hearbeat starts
        ctx = YarmaRequestContext()
        self.server.cast(ctx.to_dict(), "test")


class YarmaPublisherService(service.Service):
    def __init__(self, transport):
        super(YarmaPublisherService, self).__init__()
        self.publisher_target = messaging.Target(
            topic=cfg.CONF.default.publisher_queue,
        )
        self.transport = transport
        self.server = messaging.RPCClient(
            self.transport,
            self.publisher_target,
            serializer=messaging.JsonPayloadSerializer()
        )

    def start(self):
        while True:
            # recreate context so we get an unique uuid
            ctx = YarmaRequestContext()
            self.server.cast(ctx.to_dict(), "test")
            LOG.info("Sent message {} with timestamp {}".format(ctx.uuid, ctx.timestamp))
            eventlet.sleep(cfg.CONF.default.send_msg_every)


class RabbitMonitoringAgent:
    def __init__(self):
        conf = cfg.CONF.default

        self.transport = messaging.get_transport(cfg.CONF, url=conf.transport_url)

        LOG.info("Starting")

    def heartbeat_start(self):
        launcher = service.ProcessLauncher(cfg.CONF, restart_method="mutate")
        heartbeat = YarmaHearbeatService(self.transport)
        launcher.launch_service(heartbeat)
        launcher.wait()

    def consumer_start(self):
        launcher = service.ProcessLauncher(cfg.CONF, restart_method="mutate")
        consumer = YarmaConsumerService(self.transport)
        launcher.launch_service(consumer)
        launcher.wait()

    def publisher_start(self):
        launcher = service.ProcessLauncher(cfg.CONF, restart_method="mutate")
        publisher = YarmaPublisherService(self.transport)
        launcher.launch_service(publisher)
        launcher.wait()

    def start_all(self):
        services = service.Services()
        consumer = YarmaConsumerService(self.transport)
        publisher = YarmaPublisherService(self.transport)
        services.add(consumer)
        services.add(publisher)
        services.wait()


def main():
    agent = RabbitMonitoringAgent()
    if cfg.CONF.launch == "heartbeat":
        exit(agent.heartbeat_start())
    elif cfg.CONF.launch == "consumer":
        exit(agent.consumer_start())
    elif cfg.CONF.launch == "publisher":
        exit(agent.publisher_start())
    elif cfg.CONF.launch == "all":
        exit(agent.start_all())
