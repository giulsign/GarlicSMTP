# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.pipeline.stage import PipelineStage

from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager


class QueueStage(PipelineStage):

    def __init__(self, queue: QueueManager):

        self.queue = queue

    def process(self, context):

        item = QueueFactory.create(
            context.message
        )

        self.queue.enqueue(item)