from dataclasses import dataclass 

from garlicsmtp.models import MailMessage 

@dataclass 

class PipelineContext: 
	message: MailMessage 
	accepted: bool = True 
	reject_reason: str = "" 
	transport: str = "onion"
