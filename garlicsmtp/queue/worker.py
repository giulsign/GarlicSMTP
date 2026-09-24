# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.service import Service
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.core.tickable import Tickable
from garlicsmtp.logger import Logger
from garlicsmtp.exceptions import TemporaryDeliveryError
from garlicsmtp.exceptions import PermanentDeliveryError
from garlicsmtp.queue.retry import RetryPolicy



class QueueWorker(Service, Tickable):

    def __init__(
        self,
        queue: QueueManager,
        transport: TransportManager,
        logger: Logger | None = None,
        retry_policy=None,
    ):
        self.queue = queue
        self.transport = transport
        self.logger = logger or Logger()
        self.running = False
        self.retry_policy = retry_policy or RetryPolicy()
        
    
    def process(self):

        item = self.queue.peek()

        if item is None:
            return False

        if not item.ready():
            return False

        try:
            delivered = self.transport.deliver(item)

        except TemporaryDeliveryError as exc:

            item.attempts += 1

            item.last_error = (
                type(exc).__name__
            )

            item.next_retry = self.retry_policy.next_retry(
                item.attempts
            )

            self.queue.update(item)

            self.queue.nack(item)

            raise

        except PermanentDeliveryError:
            self.queue.ack(item)
            raise


        if delivered:
            self.queue.ack(item)
        else:
            self.queue.nack(item)

        return delivered

    
    def start(self):
        self.running = True
        self.logger.info("QueueWorker started")

    
    def stop(self):
        self.running = False
        self.logger.info("QueueWorker stopped")


    def tick(self):
        if not self.running:
            return

        try:
            self.process()
        except Exception as exc:
            self.logger.error(
                "QueueWorker error "
                f"[{type(exc).__name__}]"
            )