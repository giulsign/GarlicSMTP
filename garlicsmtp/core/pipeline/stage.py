# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC 

from abc import abstractmethod 

class PipelineStage(ABC): 
	
	@abstractmethod 
	
	def process(self, context): 
	
		pass
