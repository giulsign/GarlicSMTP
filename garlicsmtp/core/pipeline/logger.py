# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from .stage import PipelineStage


class LoggerStage(PipelineStage):

    def process(self, context):
        del context

        print("PIPELINE message accepted")