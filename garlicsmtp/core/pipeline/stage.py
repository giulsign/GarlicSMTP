from abc import ABC 

from abc import abstractmethod 

class PipelineStage(ABC): 
	
	@abstractmethod 
	
	def process(self, context): 
	
		pass
