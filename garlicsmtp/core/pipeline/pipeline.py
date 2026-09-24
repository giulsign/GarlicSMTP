# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


class Pipeline:

    def __init__(self):

        self.stages = []

    def add(self, stage):

        self.stages.append(stage)

    def execute(self, context):

        for stage in self.stages:

            stage.process(context)

            if not context.accepted:

                break

        return context
