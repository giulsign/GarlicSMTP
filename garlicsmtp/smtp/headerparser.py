""" RFC5322 Header Parser """ 
class HeaderParser: 
	@staticmethod 

	def parse(lines): 
	
		headers = {} 
			
		current = None 
		
		for line in lines: 
		
			# 
			# Header continuato (RFC5322 Folding) 
			# 
			
			if line.startswith((" ", "\t")): 
			
				if current is not None: 
				
					headers[current] += " " + line.strip() 
					
				continue 
				
			if ":" not in line: 
			
				continue 
				
			key, value = line.split(":", 1) 
			
			key = key.strip() 
			
			value = value.strip() 	
			
			headers[key] = value 
			
			current = key 
			
		return headers
