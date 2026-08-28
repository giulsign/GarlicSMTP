# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
